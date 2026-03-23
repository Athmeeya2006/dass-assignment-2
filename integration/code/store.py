from models import Car, CrewMember, InventoryItem, Mission, Race


class Store:
    def __init__(self):
        self.crew_members: dict = {}
        self.cars: dict = {}
        self.races: dict = {}
        self.missions: dict = {}
        self.inventory_items: dict = {}
        self.cash_balance: float = 10000.0
        self.race_rankings: list = []
        self.repair_log: list = []

    def reset(self):
        self.__init__()


store = Store()
