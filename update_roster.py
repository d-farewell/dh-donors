from roster import Roster
from contributors import Contributor, process_contributions
from csv import reader, writer
from update_orders import update_donor_orders, order_fulfillments

r = Roster(load_from_file="inputs/roster.txt")
# r = Roster()


r.save()

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


with open("inputs/roster.txt", 'r', encoding="utf_8") as f:
    r = reader(f, delimiter=';')
    # data = list(r)
    # return data
    for line in r:
        donor_name = line[0]
        if donor_name in donors:
            donors[donor_name].char_class = line[3]
            donors[donor_name].level = int(line[2])

update_donor_orders(donors)