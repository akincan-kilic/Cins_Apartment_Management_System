class ClientCard:
    def __init__(self, name, apartment_no):
        self.name = name
        self.apartment_no = apartment_no
        self.id = self.generate_id()

    def generate_id(self):
        return f"{self.name}_{self.apartment_no}"
