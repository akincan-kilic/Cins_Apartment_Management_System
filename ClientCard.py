import custom_exceptions as ce


class ClientCard:
    def __init__(self, name: str, apartment_no: int):
        if not isinstance(name, str):
            raise ce.NameShouldBeStringError("Name is not a string.")
        if not isinstance(apartment_no, int):
            raise ce.ApartmentNoShouldBeIntegerError("Apartment number is not an integer.")

        self.name = name
        self.apartment_no = apartment_no
        self.id = self.generate_id()

    def generate_id(self):
        return f"{self.name}_{self.apartment_no}"
