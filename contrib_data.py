
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
    
    if points < 50000:
        return f"Exalted: {points} / 50000"
    points -= 50000
    
    if points < 50000:
        return f"Exalted - Prestige I: {points} / 50000"
    points -= 50000
    
    if points < 50000:
        return f"Exalted - Prestige II: {points} / 50000"
    points -= 50000
    
    if points < 50000:
        return f"Exalted - Prestige III: {points} / 50000"
    points -= 50000
    
    if points < 50000:
        return f"Exalted - Prestige IV: {points} / 50000"
    points -= 50000
    
    if points < 50000:
        return f"Exalted - Prestige V: {points} / 50000"
    points -= 50000
    
    return f"Too high to track: {points} above max!"
    

def process_and_post_data():
    """
    Main data processing pipeline. Loads raw contribution data, transforms it
    into point values, builds two Discord message sections:
      1. "All Time Top Contributors" — reputation scoreboard grouped by player Nickname
      2. "This week's top characters by category" — weekly leaderboard grouped by character name
    Then posts all messages to a Discord channel.
    """
    msg_list = []
    channel_id = 1437569311186223166

    # Load raw contribution data from CSV.
    # Columns: From (character name), Date, Category, Amount (raw gold/item value)
    contrib_df = load_contrib_df()

    # Convert Amount from raw values to reputation points (multiply by 10).
    # E.g. a donation worth 2.0 gold becomes 20 points.
    contrib_df["Amount"] = pd.to_numeric(contrib_df["Amount"])
    contrib_df["Amount"] = (contrib_df["Amount"] * 10).astype(int)

    # Convert Date strings (e.g. "2/1/2025") to pandas datetime objects for filtering/sorting.
    contrib_df['Date'] = pd.to_datetime(contrib_df['Date'])

    # Calculate the start of the "last week" window used to filter recent contributions.
    today = datetime.now()
    last_week_start = today - timedelta(weeks=1)


    
    
    # Load lookup tables:
    #   - users.csv: maps Discord user IDs to names (used elsewhere for role assignment)
    #   - contributors.csv: maps character names ("Contributor") to player nicknames ("Nickname").
    #     Multiple characters can map to the same Nickname (alt characters of the same player).
    with open("inputs/users.csv", encoding="utf_8") as f:
        user_id_df = pd.read_csv(f, sep="\t", encoding="utf_8")
    with open("inputs/contributors.csv", encoding="utf_8") as f:
        contributor_name_df = pd.read_csv(f, sep="\t", encoding="utf_8")

    # Left-join contribution data with the contributor nickname lookup.
    # Matches each row's "From" (character name) to "Contributor" in the lookup table,
    # adding a "Nickname" column. Characters not found in contributors.csv will have
    # Nickname = NaN — these are intentionally excluded from the all-time scoreboard
    # (groupby drops NaN keys), but still appear in the weekly category leaderboard
    # (which groups by "From" instead).
    contrib_df = contrib_df.merge(contributor_name_df, how="left", left_on="From", right_on="Contributor")

    
    # ──────────────────────────────────────────────────────────────────
    # SECTION 1: Build the "All Time Top Contributors" reputation scoreboard
    # ──────────────────────────────────────────────────────────────────

    # For each known Nickname, find the date of their most recent donation.
    # This is used later to decide whether low-point players still appear
    # on the scoreboard (they show up if they donated within the last week).
    # Rows with NaN Nickname (unknown characters) are dropped by groupby.
    latest_donations = contrib_df.groupby("Nickname", as_index=False)["Date"].max()

    # Sum all-time points per Nickname across all their characters and categories.
    # Rows with NaN Nickname are dropped — only identified players appear on the
    # all-time scoreboard. Result columns: Nickname, Amount (total points).
    totals = contrib_df.groupby("Nickname", as_index=False)["Amount"].sum()
    # Sort descending so highest-scoring players are listed first.
    totals = totals.sort_values("Amount", ascending=False, ignore_index=True)

    # Convert each player's total points into a WoW-style reputation tier string.
    # E.g. 15000 points → "Honored: 6000 / 12000" (shows progress within current tier).
    totals["Reputation"] = totals["Amount"].apply(calc_rep)

    # Merge the most-recent-donation date back onto the totals dataframe.
    # This adds a "Date" column representing when each player last donated.
    totals = totals.merge(latest_donations, on="Nickname", how="left")

    # Filter the scoreboard to only include players who either:
    #   - Have accumulated at least 3000 points (reached Friendly reputation), OR
    #   - Donated within the last week (so new/small donors can see themselves)
    # Then exclude anyone with 0 or negative points.
    totals = totals[
    (totals["Amount"] >= 3000) | (totals["Date"] >= last_week_start)
    ]
    totals = totals[(totals["Amount"] > 0)]

    # Exclude "Guild Bank" from the scoreboard (internal transfers, not player donations).
    totals = totals[totals["Nickname"] != "Guild Bank"]

    # Build Discord messages for the all-time scoreboard, organized by reputation tier.
    # Iterates top-down (highest points first). When the tier changes (e.g. Exalted → Revered),
    # a new section header is inserted. Messages are split at ~1000 chars to stay within
    # Discord's message length limit.
    msg = "# All Time Top Contributors:\n"
    rep_block = "zzzzzz"
    for i, row in enumerate(totals.itertuples(index=False), start=1):
        # Split reputation string like "Honored: 6000 / 12000" into tier name and score text.
        donor_rep, score_txt = row.Reputation.split(": ")

        # Detect when we've moved to a new reputation tier and start a new message section.
        if not rep_block in row.Reputation:
            msg_list.append(msg)
            msg = f"## {donor_rep}\n"
            rep_block = donor_rep

        # Split into a new Discord message if the current one is getting too long.
        if len(msg) > 1000:
            msg_list.append(msg)
            msg = ""

        # Format: ranked position, nickname, tier progress score.
        # Below each entry, list all known alt characters for that player (small text via -#).
        msg += f"{i}. **{row.Nickname} — {score_txt}**\n-# "
        character_list = contributor_name_df.loc[
            contributor_name_df["Nickname"] == row.Nickname, "Contributor"
        ].tolist()
        for c in character_list:
            msg += f"{c}; "
        msg += "\n"

    msg_list.append(msg)

    
    # ──────────────────────────────────────────────────────────────────
    # SECTION 2: Build the "This week's top characters by category" leaderboard
    # ──────────────────────────────────────────────────────────────────

    # Filter to only contributions from the last 7 days.
    last_week_data = contrib_df[contrib_df['Date'] >= last_week_start]

    # Aggregate points per character per category for the week.
    # Uses transform('sum') to broadcast the summed amount back onto each row,
    # then drop_duplicates collapses to one row per (From, Category) pair.
    # This groups by character name ("From"), NOT by Nickname — so individual
    # characters (including alts) are ranked separately, and unknown characters
    # (NaN Nickname) are still included.
    last_week_data['Amount'] = last_week_data.groupby(["From", "Category"])['Amount'].transform('sum')
    last_week_data = last_week_data.drop_duplicates(subset=["From", "Category"])

    # Sort all weekly contributions descending by points (used for overall ordering).
    last_week_data = last_week_data.sort_values("Amount", ascending=False)

    # Identify characters from this week that have no Nickname mapping in contributors.csv.
    # These are donors whose character names haven't been linked to a player yet.
    unidentified = last_week_data.loc[last_week_data["Nickname"].isna(), "From"].unique().tolist()

    # Print and save the list of unidentified donors for manual review.
    print("Unidentified donors:")
    print(unidentified)
    with open("outputs/unk_donors.txt", "w+", encoding="utf_8") as f:
        for u in unidentified:
            f.write(u)
            f.write("\n")

    # Build a Discord message listing up to 10 unidentified donors, asking them
    # to identify themselves in the guild's Discord channel.
    unidentified_msg = f"**\nTop unidentified donors this week:** {"; ".join(unidentified[:10])}"
    unidentified_msg += "\n*If you see your name on this list, please let us know in* https://discord.com/channels/1185713039161442356/1404343191423029359 "

    # Human-readable descriptions for each donation category, shown in the weekly leaderboard.
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

    # Group this week's data by Category, then build a top-3 leaderboard for each.
    groups = last_week_data.groupby('Category')
    category_msgs = {}
    for contrib_category, category_df in groups:
        # Skip any categories not in the known description list (e.g. "Legacy" historical data).
        if not contrib_category in category_desc:
            print(f"Skipping category: {contrib_category}")
            continue

        msg = f"**{contrib_category}** *({category_desc[contrib_category]})*\n"

        # Re-aggregate within this single-category slice to ensure each character
        # has one total per category. (This is a safety re-aggregation — the earlier
        # transform on last_week_data already summed per (From, Category), but this
        # handles any edge cases within the category subset.)
        category_df['Amount'] = category_df.groupby(["From", "Category"])['Amount'].transform('sum')
        category_df = category_df.drop_duplicates(subset=["From", "Category"])

        # Sort descending and take the top 3 characters for this category.
        category_df = category_df.sort_values(by='Amount', ascending=False)

        for i, row in enumerate(category_df.head(3).itertuples(index=False), start=1):
            msg += f"{i}. {row.From} — {row.Amount} points\n"
    
        category_msgs[contrib_category] = msg

    # Append category messages in a specific display order (crafting professions first,
    # then raw materials, then gathering) rather than alphabetical.
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

    # Append the unidentified donors notice as the final message.
    msg_list.append(unidentified_msg)

    # Send all accumulated messages to the Discord channel.
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
                if msg.author.display_name == "bot"  or msg.author.display_name == "Greatfather Winter":
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