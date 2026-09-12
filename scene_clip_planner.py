from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

SEMANTIC_MAP = BASE_DIR / "outputs" / "scene_semantic_map.json"
SCENE_MAP = BASE_DIR / "outputs" / "scene_map.json"
OUTPUT_FILE = BASE_DIR / "outputs" / "scene_clip_plan.json"


def load_json(path):
    if not path.exists():
        raise RuntimeError(f"File nahi mili: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("CineExplainAI - Scene Clip Planner")
    print("=" * 60)

    semantic = load_json(SEMANTIC_MAP)
    scene_data = load_json(SCENE_MAP)

    matches = semantic.get("results", [])

    if not matches:
        raise RuntimeError(
            "scene_semantic_map.json mein results nahi mile."
        )

    scenes = scene_data.get("scenes", [])

    if not scenes:
        raise RuntimeError(
            "scene_map.json mein scenes nahi mile."
        )

    print(f"Narration matches: {len(matches)}")
    print(f"Video scenes: {len(scenes)}")
    print()

    # --------------------------------------------------
    # Scene lookup
    # IMPORTANT:
    # scene_map.json uses "id", not "scene"
    # --------------------------------------------------

    scene_lookup = {}

    for scene in scenes:

        try:
            scene_id = int(scene["id"])
        except Exception:
            continue

        scene_lookup[scene_id] = {
            "id": scene_id,
            "start": float(scene["start"]),
            "end": float(scene["end"]),
            "duration": float(scene["duration"])
        }

    if not scene_lookup:
        raise RuntimeError(
            "Scene lookup empty hai."
        )

    ordered_scenes = sorted(
        scene_lookup.values(),
        key=lambda x: x["id"]
    )

    plans = []

    previous_scene_id = 0

    # --------------------------------------------------
    # Process every narration chunk
    # --------------------------------------------------

    for index, match in enumerate(matches, start=1):

        narration_id = match.get(
            "narration_id",
            index
        )

        narration_text = match.get(
            "narration_text",
            ""
        )

        narration_start = float(
            match.get("narration_start", 0)
        )

        narration_end = float(
            match.get(
                "narration_end",
                narration_start
            )
        )

        narration_duration = float(
            match.get(
                "narration_duration",
                narration_end - narration_start
            )
        )

        matched_scene_id = int(
            match["scene"]
        )

        # --------------------------------------------------
        # Check matched scene
        # --------------------------------------------------

        if matched_scene_id not in scene_lookup:

            print(
                f"[{index}/{len(matches)}] "
                f"Scene {matched_scene_id} nahi mila."
            )

            continue

        # --------------------------------------------------
        # Keep chronological order
        # --------------------------------------------------

        selected_scene_id = matched_scene_id

        if (
            previous_scene_id > 0
            and selected_scene_id < previous_scene_id
        ):

            print(
                f"[{index}] "
                f"Chronology correction: "
                f"{selected_scene_id} -> "
                f"{previous_scene_id}"
            )

            selected_scene_id = previous_scene_id

        if selected_scene_id not in scene_lookup:
            selected_scene_id = matched_scene_id

        # --------------------------------------------------
        # Find scene index
        # --------------------------------------------------

        start_index = None

        for i, scene in enumerate(ordered_scenes):

            if scene["id"] == selected_scene_id:
                start_index = i
                break

        if start_index is None:
            continue

        first_scene = ordered_scenes[start_index]

        clip_start = first_scene["start"]
        clip_end = first_scene["end"]

        used_scene_ids = [
            first_scene["id"]
        ]

        # --------------------------------------------------
        # Extend clip using following scenes until
        # narration duration is covered.
        # --------------------------------------------------

        current_index = start_index

        while (
            clip_end - clip_start < narration_duration
            and current_index + 1 < len(ordered_scenes)
        ):

            current_index += 1

            next_scene = ordered_scenes[current_index]

            clip_end = next_scene["end"]

            used_scene_ids.append(
                next_scene["id"]
            )

        clip_duration = clip_end - clip_start

        # --------------------------------------------------
        # Save plan
        # --------------------------------------------------

        plan = {
            "narration_id": narration_id,

            "narration_text": narration_text,

            "narration_start": narration_start,

            "narration_end": narration_end,

            "narration_duration": narration_duration,

            "matched_scene": matched_scene_id,

            "clip_start": round(
                clip_start,
                6
            ),

            "clip_end": round(
                clip_end,
                6
            ),

            "clip_duration": round(
                clip_duration,
                6
            ),

            "scene_ids": used_scene_ids,

            "confidence": float(
                match.get(
                    "confidence",
                    0
                )
            ),

            "reason": match.get(
                "reason",
                ""
            ),

            "audio": match.get(
                "audio",
                ""
            )
        }

        plans.append(plan)

        previous_scene_id = selected_scene_id

        print(
            f"[{index}/{len(matches)}] "
            f"Narration {narration_id} "
            f"-> Scene {matched_scene_id} "
            f"-> "
            f"{clip_start:.2f}s - "
            f"{clip_end:.2f}s "
            f"({clip_duration:.2f}s)"
        )

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    output = {
        "source_semantic_map": str(
            SEMANTIC_MAP
        ),

        "source_scene_map": str(
            SCENE_MAP
        ),

        "total_narration_chunks": len(matches),

        "total_clip_plans": len(plans),

        "plans": plans
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

    print(
        f"Clip plans: {len(plans)}/{len(matches)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
