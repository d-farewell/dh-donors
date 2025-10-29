from roster import Roster
from contributors import Contributor, process_contributions
from csv import reader, writer
from update_orders import expire_donor_orders, update_donor_orders, order_fulfillments
from set_discord_roles import set_dungeon_roles
import logging

current_roster = Roster(load_from_file="inputs/roster.txt")
# r = Roster()
previous_roster = Roster(load_from_file="outputs/roster_latest.txt")

logging.basicConfig(filename="logs/order_updates.log", level=logging.INFO)
# Check for dead characters
death_list = set()
for member in previous_roster.characters.values():
    name = member.char_name
    if current_roster.is_member(name):
        member_update = current_roster.characters[name]
        # Check for death tag
        if "[D]" in member_update.char_pub_note:
            death_list.add(name)
        # Check for remade (lower level) characters
        elif member_update.char_level < member.char_level:
            death_list.add(name)
        

    else:
        death_list.add(name)

logging.info(f"Graveyard: {death_list}")

set_dungeon_roles(current_roster)
expire_donor_orders(current_roster)

current_roster.save()

# interest = [
#     r.characters["Bloodknife"],
#     r.characters["Adwoid"],
#     r.characters["Sayagirl"],
#     r.characters["Ungalla"],
#     r.characters["Thrik"],
#     r.characters["Kilroth"]
# ]

# for c in interest:
#     print(f"{c.char_name}: {c.char_level} {c.char_class}, ({c.kudos} points)")

# with open("inputs/grm_log.txt", encoding="utf_8") as logfile:
#     for line in logfile:
#         r.run_event(line)

order_fulfillments()

donors = process_contributions()

# TODO this should use Roster class
with open("inputs/roster.txt", 'r', encoding="utf_8") as f:
    r = reader(f, delimiter=';')
    # data = list(r)
    # return data
    for line in r:
        donor_name = line[0]
        if donor_name in donors:
            donors[donor_name].char_class = line[3]
            donors[donor_name].level = int(line[2])


update_donor_orders(donors, current_roster, death_list)