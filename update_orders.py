from csv import reader, writer
import discord
import re

BOT_NAME = "greatfather winter#5173"


channel_ids = {
    "Alchemy": 1346170208875974826,
    "Alchemy*": 1346170208875974826,
    "Blacksmithing": 1346170279906381906,
    "Cooking": 1346170492482093229,
    "Engineering": 1346170346331701330,
    "Enchanting": 1346170311447543818,
    "Quest": 1343681789545418803,
    "Quest2": 1346172847663611946,
    "Leatherworking": 1346170388291256340,
    "Tailoring": 1346170461830123611,
    "Pro": 1373394091815207052,
    "First Aid": 1346170528876199936
}


def order_fulfillments():
    client = discord.Client(intents=discord.Intents.all())

    old_orders = []
    with open("outputs/kit_orders.txt", 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for line in r:
            old_orders.append(line)
    
    fulfilled = []
    @client.event
    async def on_ready():
        for channel_id in channel_ids.values():
            print(f"Checking channel {channel_id}...")
            channel = client.get_channel(channel_id)
            async for msg in channel.history(limit=80):
                if msg.reactions:
                    react = msg.reactions[0]
                    users = [user async for user in react.users()]
                    first_user = users[0]
                    disp_name = first_user.display_name
                    disp_name = re.sub(r"\s+", "", disp_name)
                    fulfillment = (msg.content, disp_name)
                    fulfilled.append(fulfillment)
                    # print(fulfillment)
        await client.close()
    
    client.run(DISCORD_TOKEN)
    
    bankers = {}
    orders = []
    for order in old_orders:
        if order[4] == "Posted":
            msg = f"{order[1]} x{order[2]} for {order[0]}"
            for f, user in fulfilled:
                if f == msg:
                    order[4] = "Fulfilled"
                    print(f"{user} fulfilled {f}")
                    profession = order[3]
                    if not user in bankers:
                        bankers[user] = {}
                    banker_record = bankers[user]
                    if not profession in banker_record:
                        banker_record[profession] = 0
                    banker_record[profession] += 1
                    break
        orders.append(order)

    with open("outputs/kit_orders.txt", 'w', newline='', encoding="utf_8") as f:
        w = writer(f, delimiter='\t')
        for order in orders:
            w.writerow(order)
    
    with open("inputs/donations.txt", "a") as f:
        for user in bankers:
            banker_record = bankers[user]
            for profession in banker_record:
                num = banker_record[profession]
                pts = num / 4
                f.write(f"{user} donated {num} {profession} items from the guild bank {pts} s\n")



def update_donor_orders(donors):
    client = discord.Client(intents=discord.Intents.all())

    to_post = []
    old_orders = []
    with open("outputs/kit_orders.txt", 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for line in r:
            old_orders.append(line)
    
    order_record = []
    for o in old_orders:
        order_record.append(o)
        
    
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
    
    orders = []
    for donor_name in donors:
        donor = donors[donor_name]
        for item_level, item_source, item_classes, num_classes, item_name, item_count in kit_items:
            # if donor_name == "Mtanky":
            #     print("Mtanky", item_name)
            if not donor_name in recipients:
                continue
            item_level = float(item_level)
            if item_level > donor.level * 0.9 + 8:
                continue
            if item_level < donor.level * 1.1 - 9:
                continue
            if not (donor.char_class in item_classes or item_classes == "All"):
                continue
            if item_source == "Pro" and not donor_name in pro_donors:
                continue
            order_status = "Created"
            for ordered_for, ordered_item, order_count, order_source, status in old_orders:
                if ordered_for == donor.name and ordered_item == item_name and order_count == item_count:
                    order_status = status
                    break
            new_order = False
            if order_status == "Created":
                new_order = True
                order_txt = f"{item_name} x{item_count} for {donor.name}"
                channel_id = channel_ids[item_source]
                to_post.append((channel_id, order_txt))
                
                order_status = "Posted"

            order = [donor.name, item_name, item_count, item_source, order_status]
            if new_order:
                order_record.append(order)
            orders.append(order)

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

    client.run(DISCORD_TOKEN)
    
    
    with open("outputs/kit_orders.txt", 'w', newline='', encoding="utf_8") as f:
        w = writer(f, delimiter='\t')
        for order in order_record:
            w.writerow(order)