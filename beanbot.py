import os
import random
import discord
from discord.ext import commands

# Initialize bot configuration with message content capabilities
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- IN-MEMORY REGISTRY ---
player_beans = {}        # { user_id: bean_count }
player_inventories = {}  # { user_id: ["item1", "item2"] }
locked_vaults = set()    # { user_id } (Tracks padlocks)
crowned_players = set()  # { user_id } (Tracks crown protective shield)
shielded_players = set() # { user_id } (Tracks magnum protection)
gmo_farmers = set()      # { user_id } (Tracks players with permanent forage multipliers)
arrested_players = set() # { user_id } (Tracks players currently under arrest)

# --- THE BEAN BAZAAR STOCKS & PRICING ---
SHOP_ITEMS = {
    "golden_bean_rolex": 1000,
    "bean_spank": 1500,
    "aunt_sallys_refried_bean_casserole": 7500,
    "court_defense_lawyer": 3200,
    "human_bean": 9000,
    "dehydrated_pinto": 1,
    "dad_joke_bean": 15,
    "the_mystery_legume": 30,
    "compromised_note": 11,
    "paper_clip": 3,
    "suspicious_rock": 59,
    "bonus_beans": 5,
    "bean_swap": 102,
    "old_condom": 35,
    "mystery_box": 50, 
    "crusty_rubber_duck": 52,
    "3_bean_salad": 367,
    "strange_pill": 294,
    "anonymous_psa": 66,
    "box_of_temu_tiles": 0,
    "temu_voucher": 0,
    "big_red_button": 999,
    "palm_reading": 93,
    "crown_of_beans": 418,
    "padlock": 372,
    "wooden_spoon": 8,
    "magnum_condom": 202,
    "boombox": 476
}

SHOP_STOCK = {
    "golden_bean_rolex": 2,
    "bean_spank": 3,
    "aunt_sallys_refried_bean_casserole": 1,
    "court_defense_lawyer": 5,
    "human_bean": 15,
    "dehydrated_pinto": 999,
    "dad_joke_bean": 50,
    "the_mystery_legume": 25,
    "compromised_note": 7,
    "paper_clip": 3,
    "suspicious_rock": 2,
    "bonus_beans": 999,
    "bean_swap": 2,
    "old_condom": 999,
    "mystery_box": 2,
    "crusty_rubber_duck": 3,
    "3_bean_salad": 2,
    "strange_pill": 1,
    "anonymous_psa": 2,
    "box_of_temu_tiles": 0,       # 🛑 EXPLOIT FROZEN
    "temu_voucher": 0,            # 🛑 EXPLOIT FROZEN
    "big_red_button": 1,
    "palm_reading": 5,
    "crown_of_beans": 1,
    "padlock": 0,                 
    "wooden_spoon": 3,
    "magnum_condom": 2,
    "boombox": 1
}

SECRET_SHOP_ITEMS = {
    "skeleton_key": 150,
    "gmo_bean": 500,
    "counterfeit_coin": 75
}
SECRET_SHOP_STOCK = {
    "skeleton_key": 4,       
    "gmo_bean": 3,
    "counterfeit_coin": 3
}

SUS_SHOP_ITEMS = {"engagement_ring": 1}
SUS_SHOP_STOCK = {"engagement_ring": 1}


@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"--- Werewolf Action System LIVE as {bot.user} ---")
    print("--------------------------------------------------")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!beanorrhea"):
        has_role = any(role.name == "Bean Master" for role in message.author.roles)
        if not has_role:
            await message.channel.send("❌ **Access Denied.**")
            return

        mentions = message.mentions
        if not mentions:
            await message.channel.send("❌ **Usage Error:** Mention targets! Example: `!beanorrhea @Player1`")
            return

        victim_tags = " ".join([m.mention for m in mentions])
        if len(victim_tags) > 1500:
            await message.channel.send("❌ **Error:** Too many players tagged at once!")
            return

        divider_line = "─" * 35
        panic_alert = (
            f"☣️🫘 **OFFICIAL CONTAMINATION WARNING** 🫘☣️\n"
            f"{divider_line}\n"
            f"🚨 **ATTENTION:** {victim_tags}\n\n"
            f"Medical scanners indicate you have been compromised with a highly aggressive case of **Beanorrhea**!\n"
            f"Stay paranoid. 🤢"
        )
        await message.channel.send(panic_alert)
        return

    await bot.process_commands(message)


# =========================================================================
# 1. SPECIAL EVENT MODES (!SUSSHOP & !COURT)
# =========================================================================

@bot.command(name="susshop")
async def show_sus_shop(ctx):
    header = "🤫💖 **THE SUS SHOP** 💖🤫\n`A single choice stands before you... No descriptions.`\n"
    table_text = "───────────────────────────────────────\n"
    for item, cost in SUS_SHOP_ITEMS.items():
        stock = SUS_SHOP_STOCK.get(item, 0)
        status = "OUT OF STOCK" if stock <= 0 else f"Qty: {stock}"
        table_text += f"Engagement Ring ── {cost} bn ({status})\n"
    table_text += "───────────────────────────────────────\n"
    footer = "🛍️ **To seal your destiny, use:** `!susbuy engagement_ring`"
    await ctx.send(header + table_text + footer)


@bot.command(name="susbuy")
async def buy_sus_item(ctx, item_name: str):
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()

    if item_clean != "engagement_ring":
        await ctx.send("❌ That is not an item found inside the Sus Shop.")
        return

    if buyer_id in locked_vaults:
        await ctx.send("❌ **Vault Is Locked.** Your funds are frozen; you cannot execute transactions while padlocked!")
        return

    if SUS_SHOP_STOCK["engagement_ring"] <= 0:
        await ctx.send("🚫 The ring has already been claimed! The romance is dead.")
        return

    current_balance = player_beans.get(buyer_id, 0)
    if current_balance < 1:
        await ctx.send("🙅‍♂️ You don't even have 1 bean to buy a ring? Tragic.")
        return

    player_beans[buyer_id] -= 1
    SUS_SHOP_STOCK["engagement_ring"] = 0

    divider = "💍✨" * 15
    marriage_prompt = (
        f"\n{divider}\n"
        f"🚨🔔 **HOLY BEAN MATRIMONY!** 🔔🚨\n\n"
        f"💘 {ctx.author.mention} has officially dropped 1 bean to purchase the **Engagement Ring**!\n"
        f"The stars have aligned, the vows are sealed, and the community is shaking.\n\n"
        f"🎉 **CONGRATULATIONS!** Sus has officially married **Dib**! May your collective vault remain ever prosperous! 🥂💒\n"
        f"{divider}\n"
    )
    await ctx.send(marriage_prompt)


@bot.command(name="court")
async def bean_court_prompt(ctx):
    divider = "⚖️" * 18
    court_text = (
        f"\n{divider}\n"
        f"🔨⚖️ **ORDER IN THE BEAN COURT!** ⚖️🔨\n{divider}\n"
        f"Gavel strikes echo through the room! The Honorable Judge Gizmo is presiding.\n\n"
        f"🧑‍⚖️ *\"The Defendant stands accused of Grand Larceny of Legumes, illegal distribution of unpasteurized 3-Bean Salad, and intentional malicious tampering with a padlock!\"*\n\n"
        f"💥 **OBJECTION!** *\"Your Honor, my client clearly has legal immunity via their Magnum Condom protection shield! This is absolute hearsay!\"*\n\n"
        f"🤫 **THE VERDICT:** The jury is completely deadlocked. The prosecution is crying. The defense is frantically eating raw pinto beans to destroy the evidence. \n\n"
        f"👉 **Pay a bribe or face the Bean Masters!**\n{divider}\n"
    )
    await ctx.send(court_text)


# =========================================================================
# 2. PLAYER & MASTER UTILITY COMMANDS (!BEANBANK & !BEANBAZAAR)
# =========================================================================

@bot.command(name="BeanBank")
async def check_bean_bank(ctx):
    player_id = ctx.author.id
    balance = player_beans.get(player_id, 0)
    inventory = player_inventories.get(player_id, [])
    
    status = "🎒"
    if player_id in arrested_players:
        status = "🚨⛓️ [UNDER ARREST]"
    elif player_id in locked_vaults:
        status = "🔒 [LOCKED]"
    elif player_id in crowned_players:
        status = "👑"
    
    bean_flavors = ["pinto beans", "magic beans", "jelly beans", "suspicious beans", "baked beans"]
    flavor = random.choice(bean_flavors)
    
    inv_text = ", ".join([f"`{i.replace('_', ' ').capitalize()}`" for i in inventory]) if inventory else "*Empty pockets...*"
    await ctx.send(f"🫘 {ctx.author.mention} has `{balance} {flavor}`\n{status} **Inventory Stash:** {inv_text}")


@bot.command(name="BeanBazaar")
@commands.has_role("Bean Master")
async def show_leaderboard(ctx):
    active_players = {k: v for k, v in player_beans.items() if v > 0}
    if not active_players:
        await ctx.send("📉 **The Board is Blank!**")
        return

    sorted_players = sorted(active_players.items(), key=lambda item: item[1], reverse=True)
    divider_line = "─" * 35
    board_text = f"🏆 **CURRENT BEAN STANDINGS** 🏆\n{divider_line}\n"
    
    for rank, (user_id, beans) in enumerate(sorted_players, start=1):
        try:
            member = await ctx.guild.fetch_member(user_id)
            mention_tag = member.mention
        except discord.NotFound:
            mention_tag = f"Rogue Soul (<@{user_id}>)"
            
        icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🔹")
        board_text += f"{icon} {mention_tag} ── `{beans} beans`\n"
        
    await ctx.send(board_text + f"{divider_line}")


@show_leaderboard.error
async def bean_bazaar_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ **Access Denied.** Only a designated **Bean Master** can view the complete standings layout!")


# =========================================================================
# 3. ECONOMY ENGINES (FORAGE & STEAL)
# =========================================================================

@bot.command(name="forage")
@commands.cooldown(1, 1800, commands.BucketType.user)  # ⏱️ 30 minutes (1800 seconds)
async def forage_beans(ctx):
    player_id = ctx.author.id
    
    # 🔒 PADLOCK VERIFICATION: Block all incoming/outgoing value changes
    if player_id in locked_vaults:
        await ctx.send(f"🔒 **VAULT FROZEN:** {ctx.author.mention}, your padlock is engaged! Your balance cannot increase or decrease while the lock is active.")
        return

    if random.randint(1, 100) <= 50:
        beans_lost = random.randint(5, 15)
        player_beans[player_id] = max(0, player_beans.get(player_id, 0) - beans_lost)
        await ctx.send(f"🤢 **SOUR BEAN!** {ctx.author.mention} lost **{beans_lost} beans** out of pure failure.")
        return
        
    beans_found = random.randint(5, 15)
    if player_id in gmo_farmers:
        beans_found *= 2
    player_beans[player_id] = player_beans.get(player_id, 0) + beans_found
    await ctx.send(f"🌳 **SURPRISE!** {ctx.author.mention} foraged **{beans_found} beans**! 🪙")


@bot.command(name="steal")
@commands.cooldown(1, 600, commands.BucketType.user)  # ⏱️ 10 minutes (600 seconds)
async def steal_beans(ctx, target: discord.Member):
    if ctx.author.id == target.id:
        return
    thief_id, victim_id = ctx.author.id, target.id
    
    # 🔒 PADLOCK VERIFICATION: Block all theft interactions entirely
    if thief_id in locked_vaults:
        await ctx.send(f"❌ **YOUR VAULT IS LOCKED:** You cannot steal from others while your own vault is padlocked shut!")
        return

    if victim_id in locked_vaults:
        await ctx.send(f"🔒 **PADLOCK ACTIVE!** {ctx.author.mention} slammed face-first into {target.mention}'s lock! Vault protection successfully blocked all bean movement.")
        return

    if player_beans.get(victim_id, 0) <= 0:
        await ctx.send("🍂 Target has no beans!")
        return

    if victim_id in crowned_players:
        crowned_players.remove(victim_id)
        player_beans[thief_id] = max(0, player_beans.get(thief_id, 0) - 20)
        player_beans[victim_id] = player_beans.get(victim_id, 0) + 20
        await ctx.send(f"👑💥 **CROWN COUNTER!** {target.mention}'s crown protected them! {ctx.author.mention} had to pay them **20 beans** in tribute!")
        return

    if random.randint(1, 100) <= 75:
        player_beans[thief_id] = max(0, player_beans.get(thief_id, 0) - 10)
        await ctx.send(f"🦊 **FAIL!** Gizmo intercepted {ctx.author.mention} and taxed them 10 beans.")
        return
    
    victim_stash = player_beans.get(victim_id, 0)
    stolen_amount = random.randint(max(1, int(victim_stash * 0.1)), max(2, int(victim_stash * 0.3)))
    player_beans[victim_id] -= stolen_amount
    player_beans[thief_id] = player_beans.get(thief_id, 0) + stolen_amount
    await ctx.send(f"🦝 **SUCCESS!** {ctx.author.mention} smoothly swiped **{stolen_amount} beans** from {target.mention}!")


# =========================================================================
# 4. INTERACTIVE USE ENGINE FOR ALL ITEMS
# =========================================================================

def has_item(user_id, item):
    return user_id in player_inventories and item in player_inventories[user_id]

def consume_item(user_id, item):
    player_inventories[user_id].remove(item)

async def check_shield(ctx, target):
    if target.id in shielded_players:
        shielded_players.remove(target.id)
        await ctx.send(f"🛡️🛡️ **MAGNUM IMMUNITY!** {target.mention}'s Magnum Condom deflected the entire item deployment!")
        return True
    return False


@bot.command(name="use")
async def use_item_router(ctx, item_name: str, target: discord.Member = None, *, extra: str = ""):
    uid = ctx.author.id
    item_clean = item_name.strip().lower()

    if not has_item(uid, item_clean):
        await ctx.send(f"❌ You don't have a `{item_clean}` in your stash!")
        return

    # 🔒 INTERNAL RULE: Added 'skeleton_key' to the bypass array so it can actually unlock a locked vault!
    if uid in locked_vaults and item_clean not in ["padlock", "crown_of_beans", "magnum_condom", "skeleton_key"]:
        await ctx.send("❌ **VAULT LOCK ACTIVE:** You cannot deploy items that modify balances or trigger interactive rewards while locked!")
        return

    if item_clean == "skeleton_key":
        if uid not in locked_vaults:
            await ctx.send("❌ **Vault Is Already Open:** Your vault isn't padlocked right now. Save your key for when you're actually trapped!")
            return
            
        consume_item(uid, item_clean)
        locked_vaults.remove(uid)
        
        divider = "🔓🗝️" * 10
        await ctx.send(
            f"\n{divider}\n"
            f"🔓 **VAULT UNLOCKED!** {ctx.author.mention} jammed the **Skeleton Key** into their heavy padlock!\n"
            f"With a loud *CLICK*, the lock shatters into pieces. Your funds are unfrozen and you are back in the game! 🫘💥\n"
            f"{divider}\n"
        )
        return

    elif item_clean == "gmo_bean":
        if uid in gmo_farmers:
            await ctx.send("❌ You've already mutated your fields! Your forage multiplier is already permanent.")
            return
        consume_item(uid, item_clean)
        gmo_farmers.add(uid)
        await ctx.send(f"🧬🌱 **GENETIC MUTATION:** {ctx.author.mention} ate the **GMO Bean**! Your DNA has altered. All future `!forage` rewards are now **permanently doubled**!")
        return

    elif item_clean == "golden_bean_rolex":
        consume_item(uid, item_clean)
        await ctx.send(f"⌚ {ctx.author.mention} checks their **Golden Bean Rolex**. It doesn't tell time and it does absolutely nothing, but damn do they look wealthy right now.")
        return

    elif item_clean == "bean_spank":
        if not target:
            return await ctx.send("❌ You must tag a victim to spank! Example: `!use bean_spank @username`")
        consume_item(uid, item_clean)
        await ctx.send(f"💥 **PADDLE TIME!** {ctx.author.mention} just cornered {target.mention} and **SPANKED THEM** right on the spot! The village is watching!")
        return

    elif item_clean == "aunt_sallys_refried_bean_casserole":
        if not target:
            return await ctx.send("❌ Tag someone to feed this lethal dish to! Example: `!use aunt_sallys_refried_bean_casserole @username`")
        
        if target.id in locked_vaults:
            await ctx.send(f"🔒 **VAULT BLOCKED:** {target.mention} has their padlock on! They cannot lose or gain beans from items right now.")
            return

        consume_item(uid, item_clean)
        if await check_shield(ctx, target):
            return
            
        current_victim_beans = player_beans.get(target.id, 0)
        stolen_beans = min(500, current_victim_beans)
        player_beans[target.id] = max(0, current_victim_beans - stolen_beans)
        
        await ctx.send(f"🤢 **OH NO.** {ctx.author.mention} forced {target.mention} to eat a bowl of **Aunt Sally's Refried Bean Casserole**.\n💩 Their stomach rumbles violently... **THEY JUST SOILED THEIR PANTS!** They drop **{stolen_beans} beans** in absolute panic!")
        return

    elif item_clean == "court_defense_lawyer":
        consume_item(uid, item_clean)
        await ctx.send(f"⚖️ **OBJECTION!** {ctx.author.mention} has summoned a **Court Defense Lawyer** to the stand! 🛑 **EVERYONE FREEZE AND WAIT FOR THE BEAN MASTER** 🛑")
        await bean_court_prompt(ctx)
        return

    elif item_clean == "human_bean":
        consume_item(uid, item_clean)
        await ctx.send(f"🧍 {ctx.author.mention} stands proudly with their newly purchased **Human Bean**. It doesn't move, it doesn't speak, it's just a human bean standing there. Comforting.")
        return

    elif item_clean == "dehydrated_pinto":
        consume_item(uid, item_clean)
        await ctx.send(f"🍂 {ctx.author.mention} crushes a dry pinto bean in their palm. It turns into a sad cloud of dust and blows away in the wind. Incredible waste of 1 bean.")
        return

    elif item_clean == "dad_joke_bean":
        consume_item(uid, item_clean)
        jokes = [
            "Why did the bean cross the road? To prove he wasn't chicken!",
            "What is a ghost's favorite legume? A human bean!",
            "What kind of bean can't grow in a garden? A jelly bean!",
            "Where do beans go on vacation? The El Bean-o Caravan park!",
            "What do you call a successful bean? A bean-illionaire!"
        ]
        await ctx.send(f"🎙️ **Joke Bean Activated:** \"{random.choice(jokes)}\"")
        return

    elif item_clean == "the_mystery_legume":
        consume_item(uid, item_clean)
        secret_bean = random.randint(1, 3)
        await ctx.send(f"🔮 **THE MYSTERY LEGUME GAME!** {ctx.author.mention}, I am thinking of a bean container: \n1) Garbanzo Can\n2) Lima Pod\n3) Soy Sack\n\nType your guess `1`, `2`, or `3` right now!")
        
        def check_guess(m):
            return m.author == ctx.author and m.content in ['1', '2', '3'] and m.channel == ctx.channel
            
        try:
            guess_msg = await bot.wait_for('message', check=check_guess, timeout=15.0)
            if int(guess_msg.content) == secret_bean:
                player_beans[uid] = player_beans.get(uid, 0) + 5
                await ctx.send(f"🎉 **CORRECT!** You found the hidden bean! You have been rewarded with **5 Beans**!")
            else:
                await ctx.send(f"❌ **WRONG!** It was in container #{secret_bean}. Your mystery legume rots into nothingness.")
        except:
            await ctx.send("⏰ You took too long to guess and the bean withered away!")
        return

    elif item_clean == "paper_clip":
        consume_item(uid, item_clean)
        await ctx.send(f"📎... You bent the paper clip into a completely useless wire segment. It has **no operational effect** and was tossed away.")
        return

    elif item_clean == "compromised_note":
        if not target:
            return await ctx.send("❌ Tag a target to expose!")
        consume_item(uid, item_clean)
        divider_line = "─" * 35
        await ctx.send(
            f"📝🚨 **COMPROMISED NOTE ACTIVATED!** 🚨📝\n{divider_line}\n"
            f"💥 {ctx.author.mention} has just cash-burned their Note to expose {target.mention}!\n\n"
            f"The paper trail has been handed directly over to the **Bean Masters**... \n"
            f"An executive judgment is being prepared in the shadows. Look alive. 👀"
        )

    elif item_clean == "suspicious_rock":
        if not target:
            return await ctx.send("❌ Who are you throwing this rock at?")
        if target.id in locked_vaults:
            await ctx.send(f"🔒 **VAULT BLOCKED:** {target.mention} is padlocked! Their inventory cannot be disrupted or looted by external map interactions.")
            return
        consume_item(uid, item_clean)
        if await check_shield(ctx, target):
            return
        roll = random.randint(1, 100)
        if roll <= 40:
            await ctx.send(f"🥴 **BAMBOOZLED!** {target.mention} took a direct hit to the skull and must speak in gibberish!")
        elif roll <= 80:
            lost = random.randint(5, 20)
            player_beans[target.id] = max(0, player_beans.get(target.id, 0) - lost)
            await ctx.send(f"💥💩 {target.mention} was startled so badly they dropped **{lost} beans** and soiled themselves!")
        else:
            await ctx.send(f"🦊 **GIZMO CATCH!** Gizmo caught the rock and hurled it back at {ctx.author.mention}, knocking out 10 beans!")

    elif item_clean == "bonus_beans":
        consume_item(uid, item_clean)
        win = random.randint(1, 5)
        player_beans[uid] = player_beans.get(uid, 0) + win
        await ctx.send(f"🫘📈 **JACKPOT!** {ctx.author.mention} split open the seed pouch and claimed **{win} free beans**!")

    elif item_clean == "bean_swap":
        if not target:
            return await ctx.send("❌ Who are you swapping wealth with?")
        if uid in locked_vaults or target.id in locked_vaults:
            await ctx.send("❌ **SWAP FAILED:** Balance exchanges are completely disabled if either participant has an active padlock!")
            return
        consume_item(uid, item_clean)
        my_beans = player_beans.get(uid, 0)
        their_beans = player_beans.get(target.id, 0)
        player_beans[uid], player_beans[target.id] = their_beans, my_beans
        await ctx.send(f"🔄🔮 **THE BALANCE FLIP!** {ctx.author.mention} and {target.mention} just completely swapped bank balances!")

    elif item_clean == "old_condom":
        if not target:
            return await ctx.send("❌ Tag a target to snap!")
        if target.id in locked_vaults:
            await ctx.send("❌ Target is padlocked shut.")
            return
        consume_item(uid, item_clean)
        if random.randint(1, 100) <= 50:
            player_beans[target.id] = max(0, player_beans.get(target.id, 0) - 5)
            await ctx.send(f"🎈💥 **SNAP!** An old balloon hit {target.mention} square in the eyes. They lost 5 beans!")
        else:
            player_beans[uid] = max(0, player_beans.get(uid, 0) - 5)
            await ctx.send(f"💥🤦‍♂️ **BACKFIRE!** The material snapped backward hitting {ctx.author.mention} instead! Lost 5 beans.")

    elif item_clean == "crusty_rubber_duck":
        consume_item(uid, item_clean)
        await ctx.send("🦆💤 *SQUEAK!* The crusty duck echoes across the layout...")
        keys = [k for k in player_beans.keys() if k not in locked_vaults]
        if len(keys) >= 3:
            targets = random.sample(keys, 3)
            for t in targets:
                player_beans[t] = max(0, player_beans.get(t, 0) + random.choice([-5, 5]))
            await ctx.send("🦊 **GIZMO CHAOS:** Gizmo ran wild and modified the balances of 3 unprotected participants!")

    elif item_clean == "3_bean_salad":
        await ctx.send("❌ Please handle the legendary biowarfare salad explicitly using the dedicated layout command: `!use_salad @P1 @P2 @P3`")

    elif item_clean == "strange_pill":
        consume_item(uid, item_clean)
        if random.randint(1, 100) <= 50:
            player_beans[uid] *= 2
            await ctx.send(f"💊⚡ **CRITICAL SURGE!** {ctx.author.mention}'s total bean vault value just **DOUBLED**!")
        else:
            player_beans[uid] = 0
            await ctx.send(f"🤮💀 **OVERDOSE!** The chemical compounds rejected {ctx.author.mention}. Their bank value has crashed down to **0**!")

    elif item_clean == "anonymous_psa":
        if not extra:
            return await ctx.send("❌ Include a broadcast message!")
        consume_item(uid, item_clean)
        await ctx.message.delete()
        await ctx.send(f"📢🗣️ **ANONYMOUS BROADCAST:** *\"{extra}\"*")

    elif item_clean in ["box_of_temu_tiles", "temu_voucher", "mystery_box"]:
        consume_item(uid, item_clean)
        valid_pool = [k for k, v in SHOP_STOCK.items() if v > 0]
        reward = random.choice(valid_pool) if valid_pool else "dehydrated_pinto"
        if uid not in player_inventories:
            player_inventories[uid] = []
        player_inventories[uid].append(reward)
        await ctx.send(f"🎟️🛍️ **MYSTERY RE-ROLL:** {ctx.author.mention} cashed in their cheap junk and unlocked: **{reward.replace('_', ' ').capitalize()}**!")

    elif item_clean == "big_red_button":
        consume_item(uid, item_clean)
        locked_vaults.clear()
        for k in player_beans.keys():
            player_beans[k] = 10
        await ctx.send("🚨💥 **APOCALYPSE NOW!** Every single padlock exploded and all player assets have reset to **10 beans** flat!")

    elif item_clean == "palm_reading":
        if not target:
            return await ctx.send("❌ Tag a player to spy on!")
        consume_item(uid, item_clean)
        is_locked = "LOCKED 🔒" if target.id in locked_vaults else "UNPROTECTED 🔓"
        items = player_inventories.get(target.id, [])
        await ctx.send(f"✋🔮 **MYSTIC RESULTS:** {target.mention}'s vault is currently {is_locked}. Their stash contains: `{items}`.")

    elif item_clean == "crown_of_beans":
        consume_item(uid, item_clean)
        crowned_players.add(uid)
        await ctx.send(f"👑🫘 **CORONATION:** {ctx.author.mention} put on the Crown of Beans!")

    elif item_clean == "padlock":
        consume_item(uid, item_clean)
        locked_vaults.add(uid)
        await ctx.send(f"🔒⚙️ **VAULT LOCKUP:** {ctx.author.mention} locked their vault! All incoming and outgoing bean adjustments are completely frozen.")

    elif item_clean == "wooden_spoon":
        if not target:
            return await ctx.send("❌ Tag a player to hit!")
        if uid in locked_vaults or target.id in locked_vaults:
            await ctx.send("❌ **INTERACTION DENIED:** Padlocked vaults completely block physical value extraction via wooden spoons.")
            return
        consume_item(uid, item_clean)
        player_beans[target.id] = max(0, player_beans.get(target.id, 0) - 2)
        player_beans[uid] = player_beans.get(uid, 0) + 2
        await ctx.send(f"🥄💥 **WHACK!** {ctx.author.mention} smacked {target.mention} and swiped exactly **2 beans**!")

    elif item_clean == "magnum_condom":
        consume_item(uid, item_clean)
        shielded_players.add(uid)
        await ctx.send(f"🛡️🎈 **BARRIER ENGAGED:** {ctx.author.mention} deployed a Magnum Shield.")

    elif item_clean == "boombox":
        if not target:
            return await ctx.send("❌ Tag a target to deafen!")
        consume_item(uid, item_clean)
        await ctx.send(f"📻🔊 **MAX VOLUME!** {ctx.author.mention} blasted heavy bass straight into {target.mention}'s ears.")


# =========================================================================
# 5. THE BEAN BAZAAR MARKET INTERFACE (🔤 STANDARD MONOSPACE)
# =========================================================================

@bot.command(name="shop")
async def show_shop(ctx):
    header = "✨🛒 **Welcome to the Bean Bazaar** 🛒✨\n`All items are mystery-locked & non-refundable.`\n"
    table_text = "───────────────────────────────────────\n"
    
    for item, cost in SHOP_ITEMS.items():
        stock_count = SHOP_STOCK.get(item, 0)
        clean_name = item.replace("_", " ").capitalize()
        if stock_count == 999:
            status_label = "Unlimited"
        elif stock_count <= 0:
            status_label = "Out of Stock"
        else:
            status_label = f"Qty: {stock_count}"
        
        table_text += f"{clean_name} -- {cost} bns ({status_label})\n"
        
    table_text += "───────────────────────────────────────\n"
    footer = "Buy items with: `!buy [item_name]`"
    await ctx.send(header + table_text + footer)


@bot.command(name="buy")
async def buy_item(ctx, item_name: str):
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    if buyer_id in locked_vaults:
        await ctx.send("❌ **TRANSACTION ABORTED:** Your vault balance is locked shut by a padlock. Remove the lock before executing market purchases!")
        return

    if item_clean not in SHOP_ITEMS:
        await ctx.send(f"❌ '{item_name}' isn't on the shelves!")
        return
        
    if SHOP_STOCK.get(item_clean, 0) <= 0:
        await ctx.send(f"🚫 **SOLD OUT!**")
        return
        
    if buyer_id not in player_inventories:
        player_inventories[buyer_id] = []
        
    if item_clean in player_inventories[buyer_id]:
        await ctx.send(f"🛑 You already have a copy! Max 1 per player.")
        return
        
    item_cost = SHOP_ITEMS[item_clean]
    current_balance = player_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🙅 You can't afford that. Costs `{item_cost} beans`.")
        return
        
    player_beans[buyer_id] -= item_cost
    player_inventories[buyer_id].append(item_clean)
    
    if SHOP_STOCK[item_clean] != 999:
        SHOP_STOCK[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🛍️ {ctx.author.mention} spent `{item_cost} beans` and pulled a **{clean_name}**! 💨")


# =========================================================================
# 6. SECONDARY SHOP EXCHANGES & ADMIN MASTER CONTROLS
# =========================================================================

@bot.command(name="blackmarket")
async def show_secret_shop(ctx):
    header = "🕵️ **THE UNDERGROUND BLACK MARKET** 🕵️\n"
    table_text = "```\n"
    table_text += f"Item                 | Price      | Stock\n"
    table_text += "─" * 44 + "\n"
    
    for item, cost in SECRET_SHOP_ITEMS.items():
        stock_count = SECRET_SHOP_STOCK.get(item, 0)
        clean_name = item.replace("_", " ").capitalize()
        status_label = "DEPLETED" if stock_count <= 0 else f"Qty: {stock_count}"
        table_text += f"{clean_name:<20} | {cost:<10} | {status_label:<8}\n"
        
    table_text += "```\n"
    footer = "Buy with: `!shadowbuy [item_name]`"
    await ctx.send(header + table_text + footer)


@bot.command(name="shadowbuy")
async def buy_secret_item(ctx, item_name: str):
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    if buyer_id in locked_vaults:
        await ctx.send("❌ Your vault balance is locked shut by a padlock!")
        return

    if item_clean not in SECRET_SHOP_ITEMS:
        await ctx.send("❌ That item doesn't exist in the shadows.")
        return
        
    if SECRET_SHOP_STOCK.get(item_clean, 0) <= 0:
        await ctx.send("🚫 **DEPLETED!**")
        return
        
    if buyer_id not in player_inventories:
        player_inventories[buyer_id] = []
        
    if item_clean in player_inventories[buyer_id]:
        await ctx.send("🛑 You already have one!")
        return
        
    item_cost = SECRET_SHOP_ITEMS[item_clean]
    current_balance = player_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🕵️ Come back when you're serious.")
        return
    
    player_beans[buyer_id] -= item_cost
    player_inventories[buyer_id].append(item_clean)
    SECRET_SHOP_STOCK[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🤫 {ctx.author.mention} smuggled out a **{clean_name}**! 💸")


@bot.command(name="use_salad")
async def use_salad(ctx, target1: discord.Member, target2: discord.Member, target3: discord.Member):
    buyer_id = ctx.author.id
    if not has_item(buyer_id, "3_bean_salad"):
        await ctx.send("❌ You don't have the **3 Bean Salad**!")
        return

    targets = [target1, target2, target3]
    if len(set(targets)) < 3 or buyer_id in [t.id for t in targets]:
        await ctx.send("❌ Three unique victims required!")
        return

    consume_item(buyer_id, "3_bean_salad")
    await ctx.send("Salad bowl hurled! Parsing contamination fields...")
    
    reports = []
    for t in targets:
        if t.id in shielded_players:
            shielded_players.remove(t.id)
            reports.append(f"• {t.mention} deflected with a shield!")
        else:
            reports.append(f"• {t.mention} infected with **Beanorrhea**!")
            
    await ctx.send(f"🥗☣️ **THE 3 BEAN SALAD ASSAULT:**\n" + "\n".join(reports))


@bot.command(name="game_over")
@commands.has_role("Bean Master")
async def terminate_match(ctx):
    if not player_beans:
        await ctx.send("🏁 **Game Over!** No data!")
        return

    sorted_players = sorted(player_beans.items(), key=lambda item: item[1], reverse=True)
    divider_line = "─" * 35
    summary = f"🏁🏆 **MATCH CONCLUDED!** 🏆🏁\n{divider_line}\n"
    
    for rank, (user_id, beans) in enumerate(sorted_players, start=1):
        try:
            member = await ctx.guild.fetch_member(user_id)
            mention_tag = member.mention
        except discord.NotFound:
            mention_tag = f"(<@{user_id}>)"
            
        icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🔹")
        summary += f"{icon} {mention_tag} — `{beans} beans`\n"
        
    await ctx.send(summary + f"\n{divider_line}\nUntil next round... 🫘💥")


# --- 🛠️ ADMIN CHEAT PANEL ---

@bot.command(name="add")
@commands.has_role("Bean Master")
async def quick_add(ctx, member: discord.Member, amount: int):
    player_beans[member.id] = player_beans.get(member.id, 0) + amount
    await ctx.send(f"🪙 Added {amount} to {member.mention}!")


@bot.command(name="strip")
@commands.has_role("Bean Master")
async def quick_strip(ctx, member: discord.Member, amount: int):
    player_beans[member.id] = max(0, player_beans.get(member.id, 0) - amount)
    await ctx.send(f"🪓 Stripped {amount} from {member.mention}!")


@bot.command(name="givebean")
@commands.has_permissions(administrator=True)
async def admin_give_bean(ctx, member: discord.Member, amount: int):
    player_beans[member.id] = player_beans.get(member.id, 0) + amount
    await ctx.send(f"⚡ **ADMIN INJECTION:** Granted **{amount} Beans** to {member.mention}'s account balance.")


@bot.command(name="removeitem")
@commands.has_role("Bean Master")
async def admin_remove_item(ctx, member: discord.Member, item_name: str):
    item_clean = item_name.strip().lower()
    if member.id in player_inventories and item_clean in player_inventories[member.id]:
        player_inventories[member.id].remove(item_clean)
        await ctx.send(f"🛡️ **ADMIN INTERVENTION:** Stripped `{item_clean}` directly out of {member.mention}'s stash.")
    else:
        await ctx.send(f"❌ {member.mention} doesn't carry a `{item_clean}` right now.")


@bot.command(name="additem")
@commands.has_role("Bean Master")
async def admin_add_item(ctx, member: discord.Member, item_name: str):
    item_clean = item_name.strip().lower()
    if member.id not in player_inventories:
        player_inventories[member.id] = []
    
    player_inventories[member.id].append(item_clean)
    await ctx.send(f"🎁 **ADMIN REPAIR:** Forcefully injected `{item_clean}` directly into {member.mention}'s storage vaults.")


@bot.command(name="penalty")
@commands.has_role("Bean Master")
async def admin_arrest_penalty(ctx, member: discord.Member):
    fine = random.randint(1, 150)
    if member.id in locked_vaults:
        fine = 0
        
    player_beans[member.id] = max(0, player_beans.get(member.id, 0) - fine)
    arrested_players.add(member.id)
    
    divider = "🚨" * 15
    arrest_text = (
        f"\n{divider}\n"
        f"👮‍♂️🚔 **THE BEAN POLICE HAVE ARRIVED!** 🚔👮‍♂️\n\n"
        f"🚨 **SUSPECT APPREHENDED:** {member.mention} has been thrown into local server custody!\n"
        f"⚖️ **CRIMINAL CHARGE BALANCES:** They have been put **\"UNDER ARREST\"** by the Bean Masters.\n"
        f"💸 **LEGAL FINE EXTRACTED:** `{fine} beans` were seized directly from their asset pool!\n"
        f"{divider}"
    )
    await ctx.send(arrest_text)


@forage_beans.error
@steal_beans.error
async def cooldown_logs(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ **COOLDOWN ACTIVE:** Hold your horses! You must wait another `{int(error.retry_after // 60)}`m `{int(error.retry_after % 60)}`s before executing that action again!")


bot.run(os.environ.get("DISCORD_TOKEN"))
