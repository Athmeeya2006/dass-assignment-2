import crew_management
import garage
import inventory
import leaderboard
import mission_planning
import race_management
import registration
import results


def safe_call(func):
    try:
        result = func()
        if result is not None:
            print(result)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")


def registration_menu():
    while True:
        print("\nRegistration Menu")
        print("1) Register member")
        print("2) Get member")
        print("3) List members")
        print("4) Remove member")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(lambda: registration.register_member(input("Name: ").strip(), input("Role: ").strip()))
        elif choice == "2":
            safe_call(lambda: registration.get_member(input("Member ID: ").strip()))
        elif choice == "3":
            safe_call(registration.list_members)
        elif choice == "4":
            safe_call(lambda: registration.remove_member(input("Member ID: ").strip()))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def crew_menu():
    while True:
        print("\nCrew Menu")
        print("1) Assign role")
        print("2) Update skill")
        print("3) Set availability")
        print("4) Get available by role")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(
                lambda: crew_management.assign_role(
                    input("Member ID: ").strip(), input("New role: ").strip()
                )
            )
        elif choice == "2":
            safe_call(
                lambda: crew_management.update_skill_level(
                    input("Member ID: ").strip(), int(input("Skill (1-10): ").strip())
                )
            )
        elif choice == "3":
            safe_call(
                lambda: crew_management.set_availability(
                    input("Member ID: ").strip(),
                    input("Available? (y/n): ").strip().lower() == "y",
                )
            )
        elif choice == "4":
            safe_call(lambda: crew_management.get_available_by_role(input("Role: ").strip()))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def inventory_menu():
    while True:
        print("\nInventory Menu")
        print("1) Add car")
        print("2) Get car")
        print("3) List cars")
        print("4) Update car condition")
        print("5) Add inventory item")
        print("6) Get cash balance")
        print("7) Add cash")
        print("8) Deduct cash")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(lambda: inventory.add_car(input("Car name: ").strip(), int(input("Speed (1-10): ").strip())))
        elif choice == "2":
            safe_call(lambda: inventory.get_car(input("Car ID: ").strip()))
        elif choice == "3":
            safe_call(lambda: inventory.list_cars(input("Available only? (y/n): ").strip().lower() == "y"))
        elif choice == "4":
            safe_call(
                lambda: inventory.update_car_condition(
                    input("Car ID: ").strip(), input("Condition: ").strip()
                )
            )
        elif choice == "5":
            safe_call(
                lambda: inventory.add_inventory_item(
                    input("Type (part/tool): ").strip(),
                    input("Name: ").strip(),
                    int(input("Quantity: ").strip()),
                )
            )
        elif choice == "6":
            safe_call(inventory.get_cash_balance)
        elif choice == "7":
            safe_call(lambda: inventory.add_cash(float(input("Amount: ").strip())))
        elif choice == "8":
            safe_call(lambda: inventory.deduct_cash(float(input("Amount: ").strip())))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def races_menu():
    while True:
        print("\nRaces Menu")
        print("1) Create race")
        print("2) Assign driver")
        print("3) Assign car")
        print("4) Start race")
        print("5) Get race")
        print("6) List races")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(
                lambda: race_management.create_race(
                    input("Race name: ").strip(),
                    input("Location: ").strip(),
                    float(input("Prize money: ").strip()),
                )
            )
        elif choice == "2":
            safe_call(
                lambda: race_management.assign_driver_to_race(
                    input("Race ID: ").strip(), input("Driver member ID: ").strip()
                )
            )
        elif choice == "3":
            safe_call(
                lambda: race_management.assign_car_to_race(
                    input("Race ID: ").strip(), input("Car ID: ").strip()
                )
            )
        elif choice == "4":
            safe_call(lambda: race_management.start_race(input("Race ID: ").strip()))
        elif choice == "5":
            safe_call(lambda: race_management.get_race(input("Race ID: ").strip()))
        elif choice == "6":
            filter_value = input("Status filter (blank for all): ").strip()
            safe_call(lambda: race_management.list_races(filter_value or None))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def results_menu():
    while True:
        print("\nResults Menu")
        print("1) Record result")
        print("2) Get rankings")
        print("3) Get driver stats")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(
                lambda: results.record_result(
                    input("Race ID: ").strip(),
                    input("Winner member ID: ").strip(),
                    input("Car condition after race: ").strip(),
                )
            )
        elif choice == "2":
            safe_call(results.get_rankings)
        elif choice == "3":
            safe_call(lambda: results.get_driver_stats(input("Member ID: ").strip()))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def missions_menu():
    while True:
        print("\nMissions Menu")
        print("1) Create mission")
        print("2) Assign mission")
        print("3) Complete mission")
        print("4) Fail mission")
        print("5) Get mission")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(
                lambda: mission_planning.create_mission(
                    input("Mission name: ").strip(),
                    input("Mission type: ").strip(),
                    [role.strip() for role in input("Required roles (comma-separated): ").split(",") if role.strip()],
                    input("Involves damaged car? (y/n): ").strip().lower() == "y",
                )
            )
        elif choice == "2":
            safe_call(lambda: mission_planning.assign_mission(input("Mission ID: ").strip()))
        elif choice == "3":
            safe_call(lambda: mission_planning.complete_mission(input("Mission ID: ").strip()))
        elif choice == "4":
            safe_call(
                lambda: mission_planning.fail_mission(
                    input("Mission ID: ").strip(), input("Failure reason: ").strip()
                )
            )
        elif choice == "5":
            safe_call(lambda: mission_planning.get_mission(input("Mission ID: ").strip()))
        elif choice == "0":
            return
        else:
            print("Invalid option")


def leaderboard_menu():
    while True:
        print("\nLeaderboard Menu")
        print("1) Full leaderboard")
        print("2) Top N drivers")
        print("3) Mission success rate")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(leaderboard.get_full_leaderboard)
        elif choice == "2":
            safe_call(lambda: leaderboard.get_top_driver(int(input("N: ").strip())))
        elif choice == "3":
            safe_call(leaderboard.get_mission_success_rate)
        elif choice == "0":
            return
        else:
            print("Invalid option")


def garage_menu():
    while True:
        print("\nGarage Menu")
        print("1) Repair car")
        print("2) Repair log")
        print("3) Cars needing repair")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            safe_call(
                lambda: garage.repair_car(
                    input("Car ID: ").strip(), input("Mechanic member ID: ").strip()
                )
            )
        elif choice == "2":
            safe_call(garage.get_repair_log)
        elif choice == "3":
            safe_call(garage.get_cars_needing_repair)
        elif choice == "0":
            return
        else:
            print("Invalid option")


def run_cli():
    while True:
        print("\nStreetRace Manager")
        print("1) Registration")
        print("2) Crew")
        print("3) Inventory")
        print("4) Races")
        print("5) Results")
        print("6) Missions")
        print("7) Leaderboard")
        print("8) Garage")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            registration_menu()
        elif choice == "2":
            crew_menu()
        elif choice == "3":
            inventory_menu()
        elif choice == "4":
            races_menu()
        elif choice == "5":
            results_menu()
        elif choice == "6":
            missions_menu()
        elif choice == "7":
            leaderboard_menu()
        elif choice == "8":
            garage_menu()
        elif choice == "0":
            print("Goodbye")
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    run_cli()
