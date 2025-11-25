from csv import reader, writer
import discord
import re
import logging
import datetime

logging.basicConfig(filename="logs/order_updates.log", level=logging.INFO)
logging.info(datetime.datetime.now().date())

with open("discord_token.txt") as f:
    txt = f.read()
DISCORD_TOKEN = txt
BOT_NAME = "greatfather winter#5173"


channel_ids = {
    "Alchemy": 1346170208875974826,
    "Blacksmithing": 1346170279906381906,
    "Cooking": 1346170492482093229,
    "Engineering": 1346170346331701330,
    "Enchanting": 1346170311447543818,
    "Quest": 1343681789545418803,
    "Quest2": 1346172847663611946,
    "Leatherworking": 1346170388291256340,
    "Tailoring": 1346170461830123611,
    "Pro": 1373394091815207052,
    "First Aid": 1346170528876199936,
    "Dhstorage": 1421040400797270016
}

def to_int(txt):
    ans = float(txt)
    ans = int(ans)
    return ans

class Kit_Order:
    def __init__(self):
        # Initialize default values for all attributes
        self.for_char = ""
        self.item = ""
        self.qty = -1
        self.source = ""
        self.status = ""
        self.item_level = 99
    
    def load_from_list(self, data):
        # Dynamically get all attribute names except built-in ones
        fields = [attr for attr in vars(self) if not attr.startswith("__")]

        for i, field in enumerate(fields):
            if i < len(data):
                setattr(self, field, data[i])
        
        self.item_level = to_int(self.item_level)
        try:
            self.qty = to_int(self.qty)
        except:
            print(f"WARNING: {self.item} has no set quantity")
            self.qty = 1

    def list_info(self):
        # Return a list of order values
        info = vars(self).values()
        return info
    
    def discord_message_txt(self):
        # Content of the order message to be posted to discord
        txt = f"{self.item} x{self.qty} for {self.for_char}"
        return txt
    
    def matches(self, order):
        # Check whether this order matches another order
        if not self.for_char == order.for_char:
            return False 
        if not self.item == order.item:
            return False 
        if not self.qty == order.qty:
            return False 
        # if not self.source == order.source:
        #     return False 
        if self.item_level == 99 or order.item_level == 99:
            return True
        if self.item_level - order.item_level < 1:
            return True
        return False



def load_kit_orders(filename="outputs/kit_orders.txt", death_list=[]):
    # Load orders from tsv file
    orders = []
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for line in r:
            order = Kit_Order()
            order.load_from_list(line)
            if order.for_char in death_list:
                logging.info(f"Deleting due to death: {order.discord_message_txt()}")
            else:
                orders.append(order)
    return orders

def save_kit_orders(order_list, filename="outputs/kit_orders.txt"):
    
    with open(filename, 'w', newline='', encoding="utf_8") as f:
        w = writer(f, delimiter='\t')
        for order in order_list:
            w.writerow(order.list_info())

def order_fulfillments():
    # Delete and credit fulfilled orders

    client = discord.Client(intents=discord.Intents.all())

    kit_order_list = load_kit_orders()
    
    # List of discord messages for each active order
    active_orders = set()
    for order in kit_order_list:
        if order.status == "Posted":
            active_orders.add(order.discord_message_txt())


    
    fulfilled = []
    # Event handler that runs when the bot is ready.
    @client.event
    async def on_ready():
        for channel_id in channel_ids.values():
            print(f"Checking channel {channel_id}...")
            channel = client.get_channel(channel_id)
            async for msg in channel.history(limit=200):

                # Only look at posts that were made by the bot
                poster = msg.author.display_name
                if not poster == "bot":
                    continue

                # Don't delete scoring posts
                txt = msg.content
                if "earned" in txt and "points" in txt:
                    continue
                
                # Don't delete active ("Posted") orders
                to_delete = True
                if txt in active_orders:
                    # Remove from set so there are no duplicate orders
                    active_orders.remove(txt)
                    to_delete = False

                if msg.reactions:
                    # If anyone has reacted to the order, create a fulfillment
                    # The fulfillment is a tuple of the order text and the fulfiller name
                    to_delete = True
                    print(f"Order fulfilled: {txt}")
                    react = msg.reactions[0]
                    users = [user async for user in react.users()]
                    first_user = users[0]
                    disp_name = first_user.display_name
                    disp_name = re.sub(r"\s+", "", disp_name)
                    fulfillment = (txt, disp_name)
                    fulfilled.append(fulfillment)
                    logging.info(f"{disp_name} fulfilled {txt}")

                
                
                # Delete inactive/fulfilled posts
                if to_delete:
                    await msg.delete()

        await client.close()
    
    client.run(DISCORD_TOKEN)
    
    # Banker records are used to tally fulfillments
    # Bankers (dict)
    #    key: Banker display name
    #    val: Banker record (dict)
    #       key: Profession
    #       val: Count of orders fulfilled
    bankers = {}
    for order in kit_order_list:
        # Status updates
        if order.status == "Expiring":
            order.status = "Deleted"
        if order.status == "Posted":
            msg = order.discord_message_txt()
            # Check fulfillments
            for fulfilled_msg, user in fulfilled:
                if fulfilled_msg == msg:
                    order.status = "Fulfilled"
                    print(f"{user} fulfilled {fulfilled_msg}")
                    profession = order.source

                    # Create and increment banker records
                    if not user in bankers:
                        bankers[user] = {}
                    banker_record = bankers[user]
                    if not profession in banker_record:
                        banker_record[profession] = 0
                    banker_record[profession] += 1
                    break

    # Save kit orders to file
    save_kit_orders(kit_order_list)
    
    # Give donor credit to bankers
    to_post = []
    with open("inputs/donations.txt", "a") as f:
        for user in bankers:
            banker_record = bankers[user]
            for profession in banker_record:
                num = banker_record[profession]
                pts = num / 2
                f.write(f"\n{user} donated {num} {profession} items from the guild bank {pts*100} s\n")

                channel_id = channel_ids[profession]
                post = (channel_id, f" * **{user}** earned {int(pts*10)} points!")
                to_post.append(post)


    client2 = discord.Client(intents=discord.Intents.all())

    # Event handler that runs when the bot is ready.
    @client2.event
    async def on_ready():
        print("Client Ready!)")
        for channel_id, txt in to_post:
            channel = client2.get_channel(channel_id)
            if channel:
                await channel.send(txt)
            else:
                print("Channel not found!")
                print(f"Channel {channel_id}\nScoring: {to_post}")
        await client2.close()
    
    client2.run(DISCORD_TOKEN)

def expire_donor_orders(roster):
    
    kit_order_list = load_kit_orders()
    for order in kit_order_list:
        if order.status == "Posted":
            if roster.is_member(order.for_char):
                donor = roster.characters[order.for_char]
                if order.item_level < donor.char_level * 1.1 - 9:
                    logging.info(f"EXPIRING {order.discord_message_txt()} ({donor.char_name} leveled up to {donor.char_level})")
                    order.status = "Expiring"
            else:
                logging.info(f"EXPIRING {order.discord_message_txt()} ({order.for_char} missing from roster)")
                order.status = "Expiring"

    save_kit_orders(kit_order_list)

def update_donor_orders(donors, roster, death_list):
    client = discord.Client(intents=discord.Intents.all())

    to_post = []
    # Load orders
    kit_order_list = load_kit_orders(death_list=death_list)
    
    # order_record = []
    # for o in kit_order_list:
    #     order_record.append(o)
    # for order in kit_order_list:
    #     order_record.append(order.copy())
        # if ordered_for in donors:
        #     donor = donors[ordered_for]
        #     if item_level < donor.level * 1.1 - 9:
        #         if status == "Posted":
        #             status = "Expiring"
        # o = ordered_for, ordered_item, order_count, order_source, status
    
    
    
    kit_items = []
    with open("item_tracking/leveling_kit.txt", 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for line in r:
            kit_items.append(line)

    recipients = []
    with open("inputs/recipients.txt", "r", encoding="utf_8") as f:
        for line in f:
            recipients.append(line.strip())

    pro_donors = []
    with open("inputs/pro_donors.txt", "r", encoding="utf_8") as f:
        for line in f:
            pro_donors.append(line.strip())
    
    non_recipients = set()
    # Loop through current donors and create kit orders
    for donor_name in donors:
        donor = donors[donor_name]
        try:
            character = roster.characters[donor_name]
        except:
            continue
        for item_level, item_source, item_classes, num_classes, item_name, item_count in kit_items:
            # Pass checks to see if it's a valid order
            if not donor_name in recipients:
                if donor.level > 5 and donor.level < 42:
                    # Alts lvl 5 and under are usually bank alts
                    # Alts closer to 60 often don't need supplies
                    non_recipients.add(donor_name)
                continue
            item_level = float(item_level)
            if item_level > donor.level * 0.9 + 9:
                continue
            if item_level < donor.level * 1.1 - 10:
                continue
            if "[D]-20" in character.char_pub_note:
                continue
            if not (donor.char_class in item_classes or item_classes == "All"):
                continue
            if item_source == "Pro" and not donor_name in pro_donors:
                continue
            if "Green Hills" in item_name and "GH" in character.char_officer_note:
                continue
            
            # Create the new order
            new_order = Kit_Order()
            new_order.load_from_list([
                donor_name,
                item_name,
                item_count,
                item_source,
                "Created",
                int(item_level)
            ])


            # Check if the order already exists
            for order in kit_order_list:
                if "Whirlwind" in order.item and "Whirlwind" in new_order.item:
                    print("Whirlwind check")
                    print(order.matches(new_order))
                    print()
                if order.matches(new_order):
                    new_order.status = order.status
                    break
            

            if new_order.status == "Created":
                # Create the discord message and get ready to post
                channel_id = channel_ids[item_source]
                to_post.append((channel_id, new_order.discord_message_txt()))
                new_order.status = "Posted"

                # Add order to the list that will be saved to file
                kit_order_list.append(new_order)
                logging.info(f"Creating order: {new_order.discord_message_txt()}")


    # Print the donors who aren't signed up for leveling supplies
    print("\nDonors who aren't signed up for leveling supplies:")
    for contributor_name in non_recipients:
        print(contributor_name)
    
    @client.event
    async def on_ready():
        print("Client Ready!)")
        for channel_id, order_txt in to_post:
            channel = client.get_channel(channel_id)
            # print(f'Logged in as {client.user}')
            if channel:
                await channel.send(order_txt)
            else:
                print("Channel not found!")
                print(f"Channel {channel_id}\nOrder: {order_txt}")
        await client.close()

    # Post discord messages
    client.run(DISCORD_TOKEN)
    
    save_kit_orders(kit_order_list)