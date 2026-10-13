
from typing import Any


def recommend_structures(
    user_type: str,
    available_area_m2: float,
    roof_area_m2: float = 0,
    soil_type: str = "unknown",
    goal: str = "storage",
) -> dict[str, Any]:

    # Validate user inputs
    allowed_users = {"household", "farmer"}
    allowed_goals = {"storage", "groundwater_recharge", "irrigation"}

    user_type = user_type.strip().lower()
    goal = goal.strip().lower()
    soil_type = soil_type.strip().lower()

    if user_type not in allowed_users:
        raise ValueError("user_type must be household or farmer")

    if goal not in allowed_goals:
        raise ValueError(
            "goal must be storage, groundwater_recharge, or irrigation"
        )

    if available_area_m2 <= 0:
        raise ValueError("available_area_m2 must be greater than zero")

    if roof_area_m2 < 0:
        raise ValueError("roof_area_m2 cannot be negative")

    recommendations = []

    # Option 1: Storage tank
    if user_type == "household" and roof_area_m2 > 0:
        recommendations.append({
            "structure": "Storage tank",
            "reason": (
                "Can store harvested roof runoff for later use. "
                "Tank capacity should be calculated separately."
            ),
            "suitability": "Consider",
        })

    # Option 2: Recharge pit or trench
    if goal == "groundwater_recharge":
        recommendations.append({
            "structure": "Recharge pit or trench",
            "reason": (
                "May help recharge groundwater if soil, geology, "
                "water quality, groundwater conditions and local "
                "permissions are suitable."
            ),
            "suitability": "Needs site assessment",
        })

    # Option 3: Farm pond
    if user_type == "farmer" and goal == "irrigation":
        recommendations.append({
            "structure": "Farm pond",
            "reason": (
                "May provide seasonal water storage for irrigation. "
                "Design depends on catchment, soil permeability, "
                "rainfall, lining requirements and crop water demand."
            ),
            "suitability": "Consider after feasibility check",
        })

    # General fallback
    if not recommendations:
        recommendations.append({
            "structure": "Site assessment required",
            "reason": (
                "More information about water demand, catchment, "
                "soil and site conditions is needed."
            ),
            "suitability": "Insufficient information",
        })

    return {
        "user_type": user_type,
        "available_area_m2": available_area_m2,
        "roof_area_m2": roof_area_m2,
        "soil_type": soil_type,
        "goal": goal,
        "recommendations": recommendations,
        "disclaimer": (
            "Preliminary suggestions only; not a final engineering "
            "design or confirmation of groundwater suitability."
        ),
    }


if __name__ == "__main__":
    result = recommend_structures(
        user_type="household",
        available_area_m2=20,
        roof_area_m2=120,
        soil_type="loamy",
        goal="storage",
    )

    print("Rainwater Structure Recommendations")
    print("-" * 40)

    for item in result["recommendations"]:
        print(f"\nStructure: {item['structure']}")
        print(f"Reason: {item['reason']}")
        print(f"Suitability: {item['suitability']}")

    print(f"\nNote: {result['disclaimer']}")
