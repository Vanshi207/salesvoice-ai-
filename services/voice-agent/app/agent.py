from datetime import datetime, timedelta, timezone

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair, LLMUserAggregatorParams)
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.transports.base_transport import BaseTransport
from pipecat.workers.runner import WorkerRunner

from app.config import settings
from app.context import CallContext
from app.prompts import system_prompt
from app.recording import upload_recording
from app.tools import TOOLS, register_tools

IST = timezone(timedelta(hours=5, minutes=30))


async def run_agent(transport: BaseTransport, ctx: CallContext, handle_sigint: bool = False) -> None:
    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        settings=DeepgramSTTService.Settings(model="nova-3", language="multi", smart_format=True),
    )
    llm = GroqLLMService(
        api_key=settings.groq_api_key,
        settings=GroqLLMService.Settings(model=settings.groq_model, temperature=0.6, max_tokens=150),
    )
    tts = SarvamTTSService(
        api_key=settings.sarvam_api_key,
        settings=SarvamTTSService.Settings(model="bulbul:v3", voice=settings.sarvam_voice,
                                           language=settings.sarvam_language),
    )
    register_tools(llm, ctx)

    today = datetime.now(IST).strftime("%A %d %B %Y, %H:%M IST")
    context = LLMContext(
        messages=[{"role": "system", "content": f"{system_prompt(ctx.lead_name)}\n\nNow: {today}"}],
        tools=TOOLS,
    )
    aggregators = LLMContextAggregatorPair(
        context, user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()))
    recorder = AudioBufferProcessor()

    pipeline = Pipeline([
        transport.input(),
        stt,
        aggregators.user(),
        llm,
        tts,
        transport.output(),
        recorder,
        aggregators.assistant(),
    ])
    worker = PipelineWorker(pipeline, params=PipelineParams(enable_metrics=True, enable_usage_metrics=True))

    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        await recorder.start_recording()
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        await worker.cancel()

    @recorder.event_handler("on_audio_data")
    async def on_audio(recorder, audio: bytes, sample_rate: int, num_channels: int):
        await upload_recording(ctx, audio, sample_rate, num_channels)

    runner = WorkerRunner(handle_sigint=handle_sigint)
    await runner.add_workers(worker)
    await runner.run()
