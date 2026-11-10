def compute_metrics(segments, rep_speaker: int, duration_s: float = 0.0) -> dict:
    rep_talk = customer_talk = 0.0
    rep_questions = customer_questions = 0
    longest_monologue = current_run = 0.0
    turns = 0
    previous_speaker = None

    for seg in segments:
        length = max(seg.end_s - seg.start_s, 0.0)
        is_rep = seg.speaker == rep_speaker
        asked = seg.text.count("?")

        if is_rep:
            rep_talk += length
            rep_questions += asked
        else:
            customer_talk += length
            customer_questions += asked

        if seg.speaker != previous_speaker:
            turns += 1
            current_run = 0.0
        current_run += length
        if is_rep:
            longest_monologue = max(longest_monologue, current_run)
        previous_speaker = seg.speaker

    total_talk = rep_talk + customer_talk
    return {
        "duration_s": round(duration_s, 1),
        "rep_talk_s": round(rep_talk, 1),
        "customer_talk_s": round(customer_talk, 1),
        "rep_talk_ratio": round(rep_talk / total_talk, 2) if total_talk else 0.0,
        "longest_rep_monologue_s": round(longest_monologue, 1),
        "rep_questions": rep_questions,
        "customer_questions": customer_questions,
        "turns": turns,
    }
