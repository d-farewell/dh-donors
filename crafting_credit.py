

import discord
with open("discord_token.txt") as f:
    txt = f.read()
DISCORD_TOKEN = txt
BOT_NAME = "greatfather winter#5173"

def read_craft_channel():
    channel_id = 1389705025328119978
    client = discord.Client(intents=discord.Intents.all())
    @client.event
    async def on_ready():
        print("Client Ready!)")
        channel = client.get_channel(channel_id)
        # print(f'Logged in as {client.user}')
        if channel:
            async for msg in channel.history(limit=50):
                txt = msg.content
                print(txt)
                for reaction in msg.reactions:
                    if reaction.emoji == "✅":
                        await client.close()
                        return
                try:
                    for line in txt.split("\n"):
                        name, craft, qty = line.split()[:3]
                        # print(f"\t{name}\t{craft}\t{qty}")
                        assert len(name) > 1
                        assert craft == "crafted"
                        qty = int(qty)
                    await msg.add_reaction("✅")
                    with open("inputs/donations.txt", "a", encoding="utf_8") as f:
                        f.write(f"\n{txt}")
                    print("\tValidated")
                except:
                    await msg.add_reaction("❌")
                    print("\tInvalid")
        else:
            print("Channel not found!")
            print(f"Channel {channel_id}")
        await client.close()

    # Post discord messages
    client.run(DISCORD_TOKEN)

