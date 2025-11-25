
from datetime import datetime, timedelta
import pandas as pd

import discord
with open("discord_token.txt") as f:
    txt = f.read()
DISCORD_TOKEN = txt
BOT_NAME = "greatfather winter#5173"

def load_contrib_df():
    with open("outputs/contribution_data.csv", encoding="utf_8") as f:
        contrib_df = pd.read_csv(f, sep="\t", encoding="utf_8")
    # contrib_df.to_csv("outputs/contribution_data_backup.csv", sep="\t", encoding="utf_8")
    # print(contrib_df.head(10))

    # current_datetime  = datetime.now()
    # formatted_date_string = current_datetime.strftime("%m/%d/%Y")

    return contrib_df


def format_top_n(df, n=5):
    top_df = df.head(n)
    message = ""
    for i, row in enumerate(top_df.itertuples(index=False), start=1):
        message += f"{i}. {row.From} — {row.Amount} points\n"
    return message

def calc_rep(points):
    """
    Calculate and return a World of Warcraft–style reputation status string
    based on accumulated reputation points.

    The function evaluates the input `points` against tier thresholds and
    returns a formatted string showing the current reputation level and
    progress toward the next tier. Reputation tiers follow the standard
    progression:

        - Neutral:   0–2999 (progress shown out of 3000)
        - Friendly:  3000–8999 (progress shown out of 6000)
        - Honored:   9000–20999 (progress shown out of 12000)
        - Revered:   21000–41999 (progress shown out of 21000)
        - Exalted:   42000+ (shows surplus points beyond Exalted)

    Parameters
    ----------
    points : int
        The total reputation points accumulated.

    Returns
    -------
    str
        A human-readable string indicating the current reputation tier and
        progress toward the next threshold, or surplus points if Exalted.
    """
    if points < 3000:
        return f"Neutral: {points} / 3000"
    points -= 3000

    if points < 6000:
        return f"Friendly: {points} / 6000"
    points -= 6000
    
    if points < 12000:
        return f"Honored: {points} / 12000"
    points -= 12000
    
    if points < 21000:
        return f"Revered: {points} / 21000"
    points -= 21000
    
    return f"Exalted: {points} / max!"
    

def process_and_post_data():
    msg_list = []
    channel_id = 1437569311186223166
    contrib_df = load_contrib_df()

    contrib_df["Amount"] = pd.to_numeric(contrib_df["Amount"])        # ensure it's numeric
    contrib_df["Amount"] = (contrib_df["Amount"] * 10).astype(int)  # multiply by 10, then convert to integer
    # print("Convert to points")
    # print(contrib_df.head())
    # print()


    contrib_df['Date'] = pd.to_datetime(contrib_df['Date'])
    # print("Convert to datetime")
    # print(contrib_df.head())
    # print()

    
    today = datetime.now()
    last_week_start = today - timedelta(weeks=1)


    
    
    with open("inputs/users.csv", encoding="utf_8") as f:
        user_id_df = pd.read_csv(f, sep="\t", encoding="utf_8")
    with open("inputs/contributors.csv", encoding="utf_8") as f:
        contributor_name_df = pd.read_csv(f, sep="\t", encoding="utf_8")

    contrib_df = contrib_df.merge(contributor_name_df, how="left", left_on="From", right_on="Contributor")
    # print("Add nicknames:")
    # print(contrib_df.head(10))
    # print()

    
    latest_donations = contrib_df.groupby("Nickname", as_index=False)["Date"].max()
    # print("Get latest donations:")
    # print(latest_donations.head(10))
    # print("...")
    # print(latest_donations.tail(20))
    # print()

    totals = contrib_df.groupby("Nickname", as_index=False)["Amount"].sum()
    totals = totals.sort_values("Amount", ascending=False, ignore_index=True)
    # print("Totals:")
    # print(totals.head(10))
    # print()

    totals["Reputation"] = totals["Amount"].apply(calc_rep)
    # print("Totals:")
    # print(totals.head(10))
    # print("...")
    # print(totals.tail(20))
    # print()


    totals = totals.merge(latest_donations, on="Nickname", how="left")
    # print("Totals, add latest date:")
    # print(totals.head(10))
    # print("...")
    # print(totals.tail(20))
    # print()

    totals = totals[
    (totals["Amount"] >= 3000) | (totals["Date"] >= last_week_start)
    ]
    # print("Filtered Totals:")
    # print(totals.head(10))
    # print("...")
    # print(totals.tail(20))
    # print()

    # Print out all top contributors
    totals = totals[totals["Nickname"] != "Guild Bank"]
    msg = "# All Time Top Contributors:\n## Exalted\n"
    rep_block = "Exalted"
    for i, row in enumerate(totals.itertuples(index=False), start=1):
        donor_rep, score_txt = row.Reputation.split(": ")
        if not rep_block in row.Reputation:
            msg_list.append(msg)
            msg = f"## {donor_rep}\n"
            rep_block = donor_rep
        # if "Neutral:" in row.Reputation:
        #     msg += "\n*You need 3000 points to reach Friendly rank to show on this list! (scoreboard is WIP, this may change)*"
        #     break
        if len(msg) > 1000:
            msg_list.append(msg)
            msg = ""

        msg += f"{i}. **{row.Nickname} — {score_txt}**\n-# "
        character_list = contributor_name_df.loc[
            contributor_name_df["Nickname"] == row.Nickname, "Contributor"
        ].tolist()
        for c in character_list:
            msg += f"{c}; "
        msg += "\n"
        # print(msg)
        # print()
    # print(msg)
    # print()
    msg_list.append(msg)
    
    # send_disc_msg(msg)
    # msg_list.append(msg)
    # for m in msg_list:
    #     print(m)
    #     print("~~~~\n")
    # print()

    
    last_week_data = contrib_df[contrib_df['Date'] >= last_week_start]
    # print("Filter to last week:")
    # print(last_week_data.head())
    # print()
    last_week_data['Amount'] = last_week_data.groupby(["From", "Category"])['Amount'].transform('sum')
    last_week_data = last_week_data.drop_duplicates(subset=["From", "Category"])
    # print("Last week grouped:")
    # print(last_week_data.head())
    # print()
    last_week_data = last_week_data.sort_values("Amount", ascending=False)
    # print("Sort from last week:")
    # print(last_week_data.head())
    # print()
    unidentified = last_week_data.loc[last_week_data["Nickname"].isna(), "From"].unique().tolist()
    # print("Top unknowns from last week:")
    # print(unidentified)
    # print()
    print("Unidentified donors:")
    print(unidentified)
    unidentified_msg = f"**\nTop unidentified donors this week:** {"; ".join(unidentified[:10])}"
    unidentified_msg += "\n*If you see your name on this list, please let us know!*"

    category_desc = {
        "Alchemy": "Potions, elixirs, etc.",
        "Blacksmithing": "Weapons, armor, etc.",
        "Cloth": "Linen Cloth, Wool Cloth, etc.",
        "Cooking": "Cooked food",
        "Enchanting": "Dust, shards, oils, etc.",
        "Engineering": "Crafted guns, bombs, etc.",
        "First Aid": "Crafted bandages and anti-venom",
        "Fishing": "Fish and rum",
        "Gear": "Gear, especially rare and epic items",
        "Herbalism": "Gathered herbs",
        "Leatherworking": "Crafted gear, armor kits, etc.",
        "Meat": "Raw meat",
        "Mining": "Ore, stones, etc.",
        "Quest": "Tradeable quest items",
        "Skinning": "Leather, hides, etc.",
        "Tailoring": "Crafted gear, bags, etc.",
        "Banking": "Fulfillment of leveling supply orders"
    }

    msg = "\n# This week's top characters by category:\n\n"
    msg_list.append(msg)
    # Top contributor breakdown by category 
    groups = last_week_data.groupby('Category')
    category_msgs = {}
    for contrib_category, category_df in groups:
        if not contrib_category in category_desc:
            print(f"Skipping category: {contrib_category}")
            continue
        # print("\n\n")
        # print(contrib_category)
        # print(category_df.head(20))
        # print()

        msg = f"**{contrib_category}** *({category_desc[contrib_category]})*\n"

        category_df['Amount'] = category_df.groupby(["From", "Category"])['Amount'].transform('sum')
        category_df = category_df.drop_duplicates(subset=["From", "Category"])

        # print(category_df.head(20))
        # print()

        
        category_df = category_df.sort_values(by='Amount', ascending=False)

        # print(category_df.head(10))
        # print()

        
        for i, row in enumerate(category_df.head(3).itertuples(index=False), start=1):
            msg += f"{i}. {row.From} — {row.Amount} points\n"
    
        # print(msg)
        category_msgs[contrib_category] = msg
        # msg_list.append(msg)
    category_order_list = [
        "Alchemy",
        "Blacksmithing",
        "Cooking",
        "Engineering",
        "First Aid",
        "Leatherworking",
        "Tailoring",
        "Cloth",
        "Gear",
        "Quest",
        "Meat",
        "Fishing",
        "Banking",
        "Enchanting",
        "Herbalism",
        "Mining",
        "Skinning"
    ]
    for cat in category_order_list:
        msg_list.append(category_msgs[cat])
        # print()
    # for m in msg_list:
    #     print(m)
    #     print("~~~\n")
    msg_list.append(unidentified_msg)
    send_disc_msg(msg_list)



def send_disc_msg(message_list, channel_id=1437569311186223166):
    client = discord.Client(intents=discord.Intents.all())
    @client.event
    async def on_ready():
        print("Client Ready!)")
        channel = client.get_channel(channel_id)
        # print(f'Logged in as {client.user}')
        if channel:
            async for msg in channel.history(limit=50):
                if msg.author.display_name == "bot":
                    await msg.delete()
            for message in message_list:
                await channel.send(message)
        else:
            print("Channel not found!")
            print(f"Channel {channel_id}")
        await client.close()

    # Post discord messages
    client.run(DISCORD_TOKEN)


# process_and_post_data()