import discord
from csv import reader, writer
from roster import Roster

with open("discord_token.txt") as f:
    txt = f.read()
DISCORD_TOKEN = txt
BOT_NAME = "greatfather winter#5173"

def load_vanguard_members(filename="inputs/vanguard.txt"):
    # Load from tsv file
    vanguard = []
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for line in r:
            if line:
                vanguard.append(line)
    return vanguard

def load_dungeon_roles(filename="data/dungeon_roles.txt"):
    # Load from tsv file
    dungeon_roles = []
    with open(filename, 'r', encoding="utf_8") as f:
        r = reader(f, delimiter='\t')
        for role, min_lvl, max_lvl in r:
            role_name = f"{role} ({min_lvl}-{max_lvl})"
            dungeon_roles.append([role_name, int(min_lvl), int(max_lvl)])
    return dungeon_roles

def set_dungeon_roles(roster):
    vanguard = load_vanguard_members()
    dungeon_roles = load_dungeon_roles()
    client = discord.Client(intents=discord.Intents.all())

    def get_nickname(unk_id):
        for char_name, nickname, disc_user in vanguard:
            if int(disc_user) == unk_id:
                return nickname

    
    disc_user_roles = dict()
    # dict key is user ID
    # value is set of dungeon roles
    
    for char_name, nickname, disc_user in vanguard:
        if roster.is_member(char_name):
            char_lvl = roster.characters[char_name].char_level
        else:
            print(f"{char_name} not found in roster")
            continue
        for dungeon, min_lvl, max_lvl in dungeon_roles:
            eligible = False
            if char_lvl >= min_lvl - 2 and char_lvl <= max_lvl + 1:
                eligible = True
            if char_lvl == 60:
                eligible = False
            
            if eligible:
                i = int(disc_user)
                if i not in disc_user_roles:
                    disc_user_roles[i] = set()
                disc_user_roles[i].add(dungeon)

    # Event handler that runs when the bot is ready.
    @client.event
    async def on_ready():

        # just one guild - death happens
        print()
        for guild in client.guilds:
            # Get the Role objects from discord for each dungeon
            disc_dungeon_roles = []
            print("Dungeon roles:")
            for dungeon, min, max in dungeon_roles:
                role = discord.utils.get(guild.roles, name=dungeon)
                disc_dungeon_roles.append(role)
                print(dungeon)
            # get nicknames and the dungeon roles
            for user_id, eligible_roles in disc_user_roles.items():
                nickname = get_nickname(user_id)
                print(f"Checking user {nickname}: ")
                print(eligible_roles)

                for disc_role in disc_dungeon_roles:
                    member = guild.get_member(user_id)
                    if disc_role.name in eligible_roles:
                        if disc_role not in member.roles:
                            print(f"{nickname} got the `{disc_role.name}` role.")
                            await member.add_roles(disc_role)
                    else:
                        if disc_role in member.roles:
                            print(f"Removing {nickname} from {disc_role.name}")
                            await member.remove_roles(disc_role)
                    
                print()
                    




        await client.close()
    
    client.run(DISCORD_TOKEN)

current_roster = Roster(load_from_file="inputs/roster.txt")
set_dungeon_roles(current_roster)