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
            if int(min_lvl) == 60:
                role_name = role
            else:
                role_name = f"{role} ({min_lvl}-{max_lvl})"
            dungeon_roles.append([role_name, int(min_lvl), int(max_lvl)])
    return dungeon_roles

def set_dungeon_roles(roster):
    vanguard = load_vanguard_members()
    dungeon_roles = load_dungeon_roles()
    client = discord.Client(intents=discord.Intents.all())

    dungeoneer_report = []

    def get_nickname(unk_id):
        for char_name, nickname, disc_user in vanguard:
            if int(disc_user) == unk_id:
                return nickname

    
    disc_user_roles = dict()
    # dict key is user ID
    # value is set of dungeon roles
    
    # class_emotes = {
    #     "Druid": ":feet:",
    #     "Rogue": ":dagger:",
    #     "Hunter": ":bow_and_arrow:",
    #     "Warrior": ":crossed_swords:",
    #     "Warlock": ":smiling_imp:",
    #     "Mage": ":man_mage:",
    #     "Priest": ":church:",
    #     "Paladin": ":shield:",
    # }
    class_emotes = {
        "Druid": "<:druid_dh:1409237061352951958>",
        "Rogue": "<:rogue_dh:1409237070584610876>",
        "Hunter": "<:hunter_dh:1409237063282331780>",
        "Warrior": "<:warrior_dh:1409237253829431377>",
        "Warlock": "<:warlock_dh:1409237073839390835>",
        "Mage": "<:mage_dh:1409237065421553870>",
        "Priest": "<:priest_dh:1409237195251781804>",
        "Paladin": "<:paladin_dh:1409237066981707908>",
    }
    
    for char_name, nickname, disc_user in vanguard:
        if roster.is_member(char_name):
            character = roster.characters[char_name]
            char_lvl = character.char_level
            if "[D]" in character.char_pub_note:
                continue
            if "Month" in character.char_pub_note:
                continue
            if character.char_last_on > 28:
                continue
            if char_lvl < 15:
                continue
            char_class = roster.characters[char_name].char_class
            dungeoneer_str = f"{class_emotes[char_class]} **{char_name}** ({nickname})  -  level {char_lvl} {char_class}"
            dungeoneer_tuple = (dungeoneer_str, char_lvl)
            dungeoneer_report.append(dungeoneer_tuple)
        else:
            print(f"{char_name} not found in roster")
            continue
        for dungeon, min_lvl, max_lvl in dungeon_roles:
            eligible = False
            if char_lvl >= min_lvl - 2 and char_lvl <= max_lvl + 1:
                eligible = True
            if char_lvl == 60 and max_lvl < 60:
                eligible = False
            
            if eligible:
                i = int(disc_user)
                if i not in disc_user_roles:
                    disc_user_roles[i] = set()
                disc_user_roles[i].add(dungeon)
    

    dungeoneer_report.sort(key=lambda x: -x[1])
    dungeoneer_report_msg_wip = "**List of active <Death Happens> Dungeoneers:** "
    dungeoneer_report_msg_list = []
    bracket = 60
    for line, level in dungeoneer_report:
        if level < bracket:
            dungeoneer_report_msg_list.append(dungeoneer_report_msg_wip)
            dungeoneer_report_msg_wip = ""
            bracket -= 10
        dungeoneer_report_msg_wip = dungeoneer_report_msg_wip + "\n" + line
    dungeoneer_report_msg_list.append(dungeoneer_report_msg_wip)

    report_channel_id = 1407051977506164817

    # Event handler that runs when the bot is ready.
    @client.event
    async def on_ready():

        # just one guild - death happens
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
                # if user_id == "ID":
                #     continue
                print(user_id, eligible_roles)
                try:
                    nickname = get_nickname(user_id)
                except:
                    # TODO - not sure why but user_id is literal 'ID', should be int. users.csv header? Tried deleting header, no change.
                    continue
                # print(f"Checking user {nickname}: ")
                # print(eligible_roles)

                for disc_role in disc_dungeon_roles:
                    member = guild.get_member(user_id)
                    if disc_role.name in eligible_roles:
                        if disc_role not in member.roles:
                            print(f"{nickname} got the `{disc_role.name}` role.")
                            await member.add_roles(disc_role)
                    else:
                        if disc_role in member.roles:
                            print(f"Removing {nickname} from `{disc_role.name}`")
                            await member.remove_roles(disc_role)
                    
                    
        # Print dungeoneer report
        channel = client.get_channel(report_channel_id)
        if channel:
            # Delete old report
            async for msg in channel.history(limit=10):
                if msg.author.display_name == "bot" or msg.author.display_name == "Greatfather Winter":
                    await msg.delete()
            for dungeoneer_msg in dungeoneer_report_msg_list:
                await channel.send(dungeoneer_msg)
        else:
            print("Channel not found!")



        await client.close()
    
    client.run(DISCORD_TOKEN)

