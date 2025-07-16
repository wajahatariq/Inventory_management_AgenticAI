class InventoryManager:
    def __init__(self):
        self.inventory = []

    def add_item(self, item):
        self.inventory.append(item)

    def update_item(self, index, updated_item):
        if 0 <= index < len(self.inventory):
            self.inventory[index] = updated_item

    def delete_item(self, index):
        if 0 <= index < len(self.inventory):
            del self.inventory[index]

    def get_inventory(self):
        return self.inventory