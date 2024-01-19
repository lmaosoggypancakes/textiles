class Node:
    all_connections = []
    def __init__(self, name, desc, _id) -> None:
        self.x = self.y = 0
        self.id = _id
        self.name = name
        self.desc = desc
        self.connections = []
    
    def connect(self, node, pin1, pin2) -> None:
        """
        Creates a connection from pin `pin1` on `self` to pin `pin2` on `node`.
        """
        conn = Connection(self, node, pin1, pin2)
        if conn not in self.connections:
            self.connections.append(conn)
        if conn not in node.connections:
            node.connections.append(conn)
        if conn not in self.all_connections:
            self.all_connections.append(conn)

class Connection:
    def __init__(self, one, two, pin1, pin2) -> None:
        self.one = one
        self.two = two
        self.pin1 = pin1
        self.pin2 = pin2
        
    def __eq__(self, other):
        if self.one == other.two:
            return self.pin1 == other.pin2
        if self.two == other.one:
            return self.pin2 == other.pin1
        if self.one == other.one:
            return (self.pin1 == other.pin1 and self.pin2 == other.pin2)
        if self.two == other.two:
            return (self.pin2 == other.pin2 and self.pin1 == other.pin1)
        return False
        
    def __str__(self):
        return f"{self.one.id} <> {self.two.id}, Pin {self.pin1} <> Pin {self.pin2}"
        
