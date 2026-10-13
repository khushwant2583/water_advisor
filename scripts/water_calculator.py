
def calculate_harvestable_water(
    rainfall_mm: float,
    area_m2: float,
    runoff_coefficient: float = 0.8,
) -> dict:
    """Calculate potential rooftop rainwater collection."""

    if rainfall_mm < 0:
        raise ValueError("Rainfall cannot be negative.")

    if area_m2 <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if not 0 <= runoff_coefficient <= 1:
        raise ValueError(
            "Runoff coefficient must be between 0 and 1."
        )

    litres = rainfall_mm * area_m2 * runoff_coefficient

    return {
        "rainfall_mm": rainfall_mm,
        "area_m2": area_m2,
        "runoff_coefficient": runoff_coefficient,
        "potential_water_litres": round(litres, 2),
        "potential_water_kl": round(litres / 1000, 2),
    }


if __name__ == "__main__":
    result = calculate_harvestable_water(
        rainfall_mm=500,
        area_m2=120,
        runoff_coefficient=0.8,
    )

    for key, value in result.items():
        print(f"{key}: {value}")
