from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def cosine_sim(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(
        cosine_similarity(
            vec_a.reshape(1, -1),
            vec_b.reshape(1, -1),
        )[0][0]
    )


def compute_match_score(new_item: dict, candidate: dict) -> float:
    """Weighted text + image cosine similarity, with cross-modal fallback
    when only one side of the pair has a photo."""
    scores = []
    weights = []

    text_score = cosine_sim(new_item["text_vec_mpnet"], candidate["text_vec_mpnet"])
    scores.append(text_score)
    weights.append(0.6)

    new_img = new_item.get("image_vec_clip")
    cand_img = candidate.get("image_vec_clip")
    new_txt_clip = new_item["text_vec_clip"]
    cand_txt_clip = candidate["text_vec_clip"]

    if new_img is not None and cand_img is not None:
        scores.append(cosine_sim(new_img, cand_img))
        weights.append(0.4)
    elif new_img is not None and cand_img is None:
        scores.append(cosine_sim(new_img, cand_txt_clip))
        weights.append(0.4)
    elif new_img is None and cand_img is not None:
        scores.append(cosine_sim(new_txt_clip, cand_img))
        weights.append(0.4)

    total_weight = sum(weights)
    combined = sum(s * w for s, w in zip(scores, weights)) / total_weight
    return combined
