"""Browser dev mode (free): `python bot.py -t webrtc`, then open http://localhost:7860"""
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.transports.base_transport import TransportParams

from app.agent import run_agent
from app.config import settings
from app.context import CallContext


async def bot(runner_args: RunnerArguments):
    transport = await create_transport(runner_args, {
        "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    })
    body = runner_args.body or {}
    lead_id = body.get("lead_id") or settings.dev_lead_id
    lead_name = body.get("lead_name") or "the customer"
    user_id = body.get("user_id") or settings.dev_user_id
    user_role = body.get("user_role") or settings.dev_user_role

    ctx = CallContext(user_id=user_id, user_role=user_role,
                      lead_id=lead_id, lead_name=lead_name)
    await run_agent(transport, ctx, handle_sigint=runner_args.handle_sigint)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
