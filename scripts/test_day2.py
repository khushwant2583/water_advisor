
from water_calculator import calculate_harvestable_water
from recommend_structure import recommend_structures


def test_water_calculator():
    result = calculate_harvestable_water(500, 120, 0.8)

    assert result["potential_water_litres"] == 48000.0
    assert result["potential_water_kl"] == 48.0


def test_household_recommendation():
    result = recommend_structures(
        user_type="household",
        available_area_m2=20,
        roof_area_m2=120,
        soil_type="loamy",
        goal="storage",
    )

    assert result["recommendations"][0]["structure"] == "Storage tank"


def test_farmer_recommendation():
    result = recommend_structures(
        user_type="farmer",
        available_area_m2=500,
        soil_type="clay",
        goal="irrigation",
    )

    assert result["recommendations"][0]["structure"] == "Farm pond"


if __name__ == "__main__":
    test_water_calculator()
    test_household_recommendation()
    test_farmer_recommendation()

    print("All Day 2 tests passed!")
