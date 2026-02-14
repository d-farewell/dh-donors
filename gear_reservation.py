import datetime
from csv import reader

import discord
with open("discord_token.txt") as f:
    txt = f.read()
DISCORD_TOKEN = txt
BOT_NAME = "greatfather winter#5173"

# This is contribution amount in gold value, not rep points. It takes 1000 rep for a reservation.
TOKEN_REP_REQUIREMENT = 100

def load_gear_credit(filename="outputs/gear_credit.txt"):
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

from contributors import load_contributors

def process_reservations():
    contributors = load_contributors()
    old_credits = load_contributors(filename="outputs/gear_credit.txt")

    # print(contributors)
    # TODO VALIDATE CREDIT LOADING
    # print(old_credits)
    # exit()

    tokens = dict()
    credit_remainder = dict()

    id_table = {}
    with open("inputs/contributors.csv", encoding='utf_8') as f:
        for line in f:
            nickname, primary_name = line.rstrip().split("\t")
            id_table[nickname] = primary_name
    # print(id_table)
    # exit()
    
    def id_contributor(char_name):
        # get main name from nickname
        if char_name in id_table:
            return id_table[char_name]
        return char_name
    def add_credit(character, amt):
        # get main name from nickname
        name = id_contributor(character)
        # print(f"IDed {character} as {name}")
        # exit()

        # add to rep score tracker
        if name in credit_remainder:
            credit_remainder[name] += amt
        else:
            credit_remainder[name] = amt
        print(f"Credited {name} {amt} points, now at {credit_remainder[name]} total")
        # if has enough rep, convert that rep to a token
        while credit_remainder[name] >= TOKEN_REP_REQUIREMENT:
            credit_remainder[name] -= TOKEN_REP_REQUIREMENT
            if name in tokens:
                tokens[name] += 1
                print(f"Credited {name} with a token, now at {tokens[name]} tokens")
            else:
                tokens[name] = 1
        # exit()


    # recalculate old credits in case of name updates
    # TODO Check consolidation
    for c in old_credits.values():
        add_credit(c.name, c.score)
    # print("Consolidated credits:")
    # print(credit_remainder)
    # exit()
    # add new credits
    for c in contributors.values():
        add_credit(c.name, c.score)
    # print("Updated credits:")
    # print(credit_remainder)
    # exit()
    
    # Library of discord ids to ping users
    disc_user_ids = dict()
    with open("inputs/users.csv", encoding="utf_8") as f:
        r = reader(f, delimiter="\t")
        for name, disc_id in r:
            disc_user_ids[name] = disc_id
    # print(disc_user_ids)

    # Compile reservation messages
    msgs = []
    for player, amt in tokens.items():
        while amt > 0:
            m = f"{player} earned a gear reservation!"
            if player in disc_user_ids:
                m+= f" <@{disc_user_ids[player]}>"
            msgs.append(m)
            amt -= 1

    channel_id = 1442929403180093520
    client = discord.Client(intents=discord.Intents.all())
    # Post discord messages
    @client.event
    async def on_ready():
        print("Client Ready!)")
        channel = client.get_channel(channel_id)
        if channel:
            for m in msgs:
                await channel.send(m)
        else:
            print(f"Channel {channel_id} not found")
        await client.close()
    client.run(DISCORD_TOKEN)
    
    # Delete old tokens
    client = discord.Client(intents=discord.Intents.all())
    @client.event
    async def on_ready():
        print("Client Ready!)")
        channel = client.get_channel(channel_id)
        if channel:
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=15)
            async for msg in channel.history(limit=50):
                if msg.author.display_name == "bot"  or msg.author.display_name == "Greatfather Winter":
                    if msg.created_at < cutoff:
                        await msg.delete()
        else:
            print(f"Channel {channel_id} not found")
        await client.close()
    client.run(DISCORD_TOKEN)

    with open("outputs/gear_credit.txt", "w", encoding="utf_8") as f:
        for character, amt in credit_remainder.items():
            l = character + "\t" + str(amt) + "\n"
            # print(l)
            f.write(l)

    with open("outputs/contributors.txt", "w", encoding="utf_8") as f:
        pass


# process_reservations()