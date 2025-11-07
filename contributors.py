
from csv import reader, writer
import pandas as pd
from datetime import datetime

def load_contributors(filename="outputs/contributors.txt"):
    contributors = dict()
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        # data = list(r)
        # return data
        for line in r:
            c = Contributor()
            c.load_from_list(line)
            contributors[c.name] = c

    return contributors

def load_untracked(filename="item_tracking/untracked_items.txt"):
    untracked_list = dict()
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for itemname, qty in r:
            untracked_list[itemname] = int(qty)
    return untracked_list

def load_tracked(filename="item_tracking/tracked_items.txt"):
    tracked_list = dict()
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for itemname, val, category in r:
            tracked_list[itemname] = (category, float(val))
    return tracked_list

    
def process_contributions(filename="inputs/donations.txt", outfile="outputs/contributors.txt"):
    kudos_list = []
    contributors = load_contributors(outfile)

    tracked_item_vals = load_tracked()
    untracked_item_qtys = load_untracked()

    with open("outputs/contribution_data.csv") as f:
        contrib_df = pd.read_csv(f, sep="\t")
    contrib_df.to_csv("outputs/contribution_data_backup.csv", sep="\t")
    print(contrib_df.head(10))
    contrib_new_data = []

    current_datetime  = datetime.now()
    formatted_date_string = current_datetime.strftime("%m/%d/%Y")


    with open(filename, encoding="utf_8") as f:
        tracked_donations = dict()
        
        for kudos in f.readlines():
            if len(kudos) < 5:
                continue

            is_item = False
            kudos_words = kudos.split()
            try:
                # Process a standard format donation (Name, category, amount)
                name, category, qty = kudos_words[:3]
                qty = int(qty)
                if category == "crafted":
                    contrib_category = "Crafting"
                    amount = qty / 10
                    contrib_amount = amount
                    kudos_list.append(kudos)
                else:
                    # This should be a donation of items to Bavin
                    assert category == "donated"
                    contrib_category = "Misc."
                    amount = kudos_words[-2]
                    item = " ".join(kudos_words[3:-2])
                    amount = float(amount)
                    contrib_amount = amount
                    is_item = True
            except:
                contrib_category = "Community"
                name = kudos_words[0]
                amount = 3
                contrib_amount = amount
                kudos_list.append(kudos)


            if is_item:
                if item in tracked_item_vals:
                    # If the item has a tracked value, use that for the score. 
                    item_category, amount = tracked_item_vals[item]
                    contrib_amount = amount * qty
                    contrib_category = item_category
                    # Also track a table of values for the kudos report
                    if not name in tracked_donations:
                        tracked_donations[name] = dict()
                    if not item in tracked_donations[name]:
                        tracked_donations[name][item] = 0
                    tracked_donations[name][item] += qty
                    if item in untracked_item_qtys:
                        untracked_item_qtys.pop(item)
                else:
                    if "from the guild bank" in item:
                        contrib_category = "Banking"
                    else:
                        contrib_category = "Misc."
                    if not item in untracked_item_qtys:
                        untracked_item_qtys[item] = 0
                    untracked_item_qtys[item] += qty

            if name in contributors:
                # print(f"Adding {amount} to {name}")
                contributors[name].score += contrib_amount
            else:
                # print(f"New contributor: {name}")
                c = Contributor()
                c.name = name
                c.score = contrib_amount
                contributors[name] = c
            
            contrib_new_row = [
                name,
                formatted_date_string,
                contrib_category,
                contrib_amount
            ]
            contrib_new_data.append(contrib_new_row)
            print(contrib_new_row)

    print("New contributions df")
    contrib_new_df = pd.DataFrame(contrib_new_data, columns=["From", "Date", "Level", "Amount"])
    print(contrib_new_df.head(10))
    contrib_new_df.to_csv("outputs/new_contrib_data.csv", sep="\t")

    print("Grouping:")
    contrib_new_df['Amount'] = contrib_new_df.groupby(["From", "Date", "Level"])['Amount'].transform('sum')
    print(contrib_new_df.head(10))
    contrib_new_df.to_csv("outputs/new_contrib_data_grouped.csv", sep="\t")
    
    print("Drop dupes:")
    contrib_new_df = contrib_new_df.drop_duplicates(subset=["From", "Date", "Level"])
    print(contrib_new_df.head(10))
    contrib_new_df.to_csv("outputs/new_contrib_data_grouped.csv", sep="\t")

    print("Concatenate:")
    contrib_final_df = pd.concat([contrib_df, contrib_new_df])
    print(contrib_final_df.head(10))
    print("...")
    print(contrib_final_df.tail(10))
    contrib_final_df.to_csv("outputs/contribution_data.csv", sep="\t", index=False)

    for player, itemdict in tracked_donations.items():
        kudos_str = f"{player} donated"
        for item, qty in itemdict.items():
            kudos_str = f"{kudos_str} {qty}x {item};"
        kudos_str = f"{kudos_str}\n"
        kudos_list.append(kudos_str)

    with open("outputs/kudos.txt", "a+", encoding="utf_8") as f:
        for k in kudos_list:
            f.write(k)
    
    with open(outfile, 'w', newline='', encoding='utf_8') as f:
        out = writer(f, delimiter='\t')
        for c in contributors.values():
            # print(c.name)
            out.writerow(c.list_info())

    with open("item_tracking/untracked_items.txt", 'w', newline='', encoding='utf_8') as f:
        out = writer(f, delimiter='\t')
        for k, v in untracked_item_qtys.items():
            out.writerow([k, v])
    
    with open(filename, 'w', newline='', encoding='utf_8') as f:
        print(f"Clearing donation file: {filename}")

    return contributors


class Contributor:
    def __init__(self):
        # Initialize default values for all attributes
        self.name = ""
        self.score = 0
        self.discord_id = ""
        self.nickname = ""
        self.char_class = ""
        self.level = -10
    
    def load_from_list(self, data):
        # Dynamically get all attribute names except built-in ones
        fields = [attr for attr in vars(self) if not attr.startswith("__")]

        for i, field in enumerate(fields):
            if i < len(data):
                setattr(self, field, data[i])
        self.score = float(self.score)



    def list_info(self):
        # info = vars(self).values()
        # return info
        return [self.name, self.score]