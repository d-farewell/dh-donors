from csv import reader, writer
from player import AltChar

class Roster:
    def __init__(self, rosterfile="outputs/roster_latest.txt", load_from_file=None, eventfile="outputs/logged_events.txt"):

        self.member_names = []
        self.characters = dict()
        self.rosterfile = rosterfile
        self.kudos_file = "outputs/kudos.txt"

        if load_from_file:
            self.load_from(load_from_file)
        else:
            self.load_from(rosterfile)

        self.eventfile = eventfile
        # try:
        #     with open(self)


    def load_from(self, fname):
        with open(fname, encoding="utf_8") as f:
            r = reader(f, delimiter=';')
            data = list(r)
        
        for line in data:
            player_name = line[0]
            if not self.is_member(player_name):
                c = AltChar()
                c.load_from_list(line)
                self.member_names.append(player_name)
                self.characters[player_name] = c

    
    def is_member(self, player_name):
        if player_name in self.member_names:
            return True
        return False
        
    def save(self):
        with open(self.rosterfile, 'w', newline='', encoding='utf_8') as f:
            out = writer(f, delimiter=';')
            for  character in self.characters.values():
                out.writerow(character.list_info())
    

    def run_event(self, event):
        ts, content = event.split(" : ")
        index, timestamp = ts.split(") ")

        # with open()



        