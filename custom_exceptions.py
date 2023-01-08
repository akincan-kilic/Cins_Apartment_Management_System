class ServerAlreadyRunningError(Exception):
    pass


class ServerNotRunningError(Exception):
    pass


class InvalidPortError(Exception):
    pass


class ServerCouldNotBeClosedError(Exception):
    pass


class ClientAlreadyConnectedError(Exception):
    pass


class ClientNotConnectedError(Exception):
    pass


class ClientCouldNotBeDisconnectedError(Exception):
    pass


class ClientAlreadyRunningError(Exception):
    pass


class ClientNotRunningError(Exception):
    pass


class ClientCouldNotBeClosedError(Exception):
    pass


class ClientCouldNotSendMessageError(Exception):
    pass


class MessageQueueNotInitializedError(Exception):
    pass


class ApartmentNoShouldBeIntegerError(Exception):
    pass


class NameShouldBeStringError(Exception):
    pass
