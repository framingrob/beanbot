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

# --- THE BEAN BAZAAR STOCKS & PRICING ---
SHOP_ITEMS = {
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
    "box_of_temu_tiles": 7,
    "temu_voucher": 7,
    "big_red_button": 999,
    "palm_reading": 93,
    "crown_of_beans": 418,
    "padlock": 372,
    "wooden_spoon": 8,
    "magnum_condom": 202,
    "boombox": 476
}

SHOP_STOCK = {
    "compromised_note": 7,
    "paper_clip": 3,
    "suspicious_rock": 2,
    "bonus_beans": 999,       # UNLIMITED SUPPLY
    "bean_swap": 2,
    "old_condom": 999,        # UNLIMITED SUPPLY
    "mystery_box": 2,
    "crusty_rubber_duck": 3,
    "3_bean_salad": 2,
    "strange_pill": 1,
    "anonymous_psa": 2,
    "box_of_temu_tiles": 1,
    "temu_voucher": 999,      # UNLIMITED SUPPLY
    "big_red_button": 1,
    "palm_reading": 5,
    "crown_of_beans": 1,
    "padlock": 5,
    "wooden_spoon": 3,
    "magnum_condom": 2,
    "boombox": 1
}

# --- THE UNDERGROUND SECRET BLACK MARKET ---
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

# --- SUS SHOP CONFIGURATION ---
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

    # Handle the raw contextual string match for Beanorrhea
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
    """Displays the hidden shop layout containing the ring."""
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
    """Handles the unique proposal sequence logic."""
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()

    if item_clean != "engagement_ring":
        await ctx.send("❌ That is not an item found inside the Sus Shop.")
        return

    if SUS_SHOP_STOCK["engagement_ring"] <= 0:
        await ctx.send("🚫 The ring has already been claimed! The romance is dead.")
        return

    current_balance = player_beans.get(buyer_id, 0)
    if current_balance < 1:
        await ctx.send("🙅‍♂️ You don't even have 1 bean to buy a ring? Tragic.")
        return

    # Complete the purchase safely
    player_beans[buyer_id] -= 1
    SUS_SHOP_STOCK["engagement_ring"] = 0   # Sold out permanently

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
    """Triggers an explosive, funny courtroom legal layout sequence."""
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
    if player_id in locked_vaults: status = "🔒"
    if player_id in crowned_players: status = "👑"
    
    bean_flavors = ["pinto beans", "magic beans", "jelly beans", "suspicious beans", "baked beans"]
    flavor = random.choice(bean_flavors)
    
    inv_text = ", ".join([f"`{i.replace('_', ' ').capitalize()}`" for i in inventory]) if inventory else "*Empty pockets...*"
    await ctx.send(f"🫘 {ctx.author.mention} has `{balance} {flavor}`\n{status} **Inventory Stash:** {inv_text}")


@bot.command(name="BeanBazaar")
@commands.has_role("Bean Master")
async def show_leaderboard(ctx):
    """Admin-only master leaderboard displaying the complete game standings."""
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
@commands.cooldown(1, 3600, commands.BucketType.user)
async def forage_beans(ctx):
    player_id = ctx.author.id
    
    if player_id in locked_vaults:
        if random.randint(1, 100) <= 50:
            await ctx.send(f"🤢 **SOUR BEAN!** {ctx.author.mention} lost **{random.randint(5, 15)} beans** out of pure failure.")
        else:
            await ctx.send(f"🌳 **SURPRISE!** {ctx.author.mention} foraged **{random.randint(5, 15)} beans**! 🪙")
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
async def steal_beans(ctx, target: discord.Member):
    if ctx.author.id == target.id: return
    thief_id, victim_id = ctx.author.id, target.id
    
    if player_beans.get(victim_id, 0) <= 0:
        await ctx.send("🍂 Target has no beans!")
        return

    if victim_id in locked_vaults:
        await ctx.send(f"🔒 **PADLOCK ACTIVE!** {ctx.author.mention} slammed face-first into {target.mention}'s lock!")
        return

    if victim_id in crowned_players:
        crowned_players.remove(victim_id)
        if thief_id in locked_vaults:
            await ctx.send(f"👑💥 **CROWN COUNTER!** {target.mention}'s crown protected them! {ctx.author.mention} had to pay them **20 beans** in tribute!")
        else:
            player_beans[thief_id] = max(0, player_beans.get(thief_id, 0) - 20)
            player_beans[victim_id] = player_beans.get(victim_id, 0) + 20
            await ctx.send(f"👑💥 **CROWN COUNTER!** {target.mention}'s crown protected them! {ctx.author.mention} had to pay them **20 beans** in tribute!")
        return

    if thief_id in locked_vaults:
        if random.randint(1, 100) <= 75:
            await ctx.send(f"🦊 **FAIL!** Gizmo intercepted {ctx.author.mention} and taxed them 10 beans.")
        else:
            victim_stash = player_beans.get(victim_id, 0)
            stolen_amount = random.randint(max(1, int(victim_stash * 0.1)), max(2, int(victim_stash * 0.3)))
            await ctx.send(f"🦝 **SUCCESS!** {ctx.author.mention} smoothly swiped **{stolen_amount} beans** from {target.mention}!")
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

    # 📎 PAPER CLIP
    if item_clean == "paper_clip":
        consume_item(uid, item_clean)
        await ctx.send(f"📎... You bent the paper clip into a completely useless wire segment. It has **no operational effect** and was tossed away.")
        return

    # 📝 COMPROMISED NOTE
    elif item_clean == "compromised_note":
        if not target: return await ctx.send("❌ Tag a target to expose!")
        consume_item(uid, item_clean)
        divider_line = "─" * 35
        await ctx.send(
            f"📝🚨 **COMPROMISED NOTE ACTIVATED!** 🚨📝\n{divider_line}\n"
            f"💥 {ctx.author.mention} has just cash-burned their Note to expose {target.mention}!\n\n"
            f"The paper trail has been handed directly over to the **Bean Masters**... \n"
            f"An executive judgment is being prepared in the shadows. Look alive. 👀"
        )

    # 🪨 SUSPICIOUS ROCK
    elif item_clean == "suspicious_rock":
        if not target: return await ctx.send("❌ Who are you throwing this rock at?")
        consume_item(uid, item_clean)
        if await check_shield(ctx, target): return
        roll = random.randint(1, 100)
        if roll <= 40:
            await ctx.send(f"🥴 **BAMBOOZLED!** {target.mention} took a direct hit to the skull and must speak in gibberish!")
        elif roll <= 80:
            lost = random.randint(5, 20)
            if target.id not in locked_vaults: player_beans[target.id] = max(0, player_beans.get(target.id, 0) - lost)
            await ctx.send(f"💥💩 {target.mention} was startled so badly they dropped **{lost} beans** and soiled themselves!")
        else:
            if uid not in locked_vaults: player_beans[uid] = max(0, player_beans.get(uid, 0) - 10)
            await ctx.send(f"🦊 **GIZMO CATCH!** Gizmo caught the rock and hurled it back at {ctx.author.mention}, knocking out 10 beans!")

    # 🫘 BONUS BEANS (1-5 range preference)
    elif item_clean == "bonus_beans":
        consume_item(uid, item_clean)
        win = random.randint(1, 5) 
        if uid not in locked_vaults: player_beans[uid] = player_beans.get(uid, 0) + win
        await ctx.send(f"🫘📈 **JACKPOT!** {ctx.author.mention} split open the seed pouch and claimed **{win} free beans**!")

    # 🔄 BEAN SWAP
    elif item_clean == "bean_swap":
        if not target: return await ctx.send("❌ Who are you swapping wealth with?")
        consume_item(uid, item_clean)
        if uid in locked_vaults or target.id in locked_vaults:
            await ctx.send(f"🔄🔮 **THE BALANCE FLIP!** {ctx.author.mention} and {target.mention} just completely swapped bank balances!")
            return
        my_beans = player_beans.get(uid, 0)
        their_beans = player_beans.get(target.id, 0)
        player_beans[uid], player_beans[target.id] = their_beans, my_beans
        await ctx.send(f"🔄🔮 **THE BALANCE FLIP!** {ctx.author.mention} and {target.mention} just completely swapped bank balances!")

    # 🎈 OLD CONDOM
    elif item_clean == "old_condom":
        if not target: return await ctx.send("❌ Tag a target to snap!")
        consume_item(uid, item_clean)
        if random.randint(1, 100) <= 50:
            if target.id not in locked_vaults: player_beans[target.id] = max(0, player_beans.get(target.id, 0) - 5)
            await ctx.send(f"🎈💥 **SNAP!** An old balloon hit {target.mention} square in the eyes. They lost 5 beans!")
        else:
            if uid not in locked_vaults: player_beans[uid] = max(0, player_beans.get(uid, 0) - 5)
            await ctx.send(f"💥🤦‍♂️ **BACKFIRE!** The material snapped backward hitting {ctx.author.mention} instead! Lost 5 beans.")

    # 🦆 CRUSTY RUBBER DUCK
    elif item_clean == "crusty_rubber_duck":
        consume_item(uid, item_clean)
        await ctx.send("🦆💤 *SQUEAK!* The crusty duck echoes across the layout...")
        keys = list(player_beans.keys())
        if len(keys) >= 3:
            targets = random.sample(keys, 3)
            for t in targets: 
                if t not in locked_vaults: player_beans[t] = max(0, player_beans.get(t, 0) + random.choice([-5, 5]))
            await ctx.send("🦊 **GIZMO CHAOS:** Gizmo ran wild and modified the balances of 3 random participants!")

    # 🥗 3 BEAN SALAD
    elif item_clean == "3_bean_salad":
        await ctx.send("❌ Please handle the legendary biowarfare salad explicitly using the dedicated layout command: `!use_salad @P1 @P2 @P3`")

    # 💊 STRANGE PILL
    elif item_clean == "strange_pill":
        consume_item(uid, item_clean)
        if random.randint(1, 100) <= 50:
            if uid not in locked_vaults: player_beans[uid] *= 2
            await ctx.send(f"💊⚡ **CRITICAL SURGE!** {ctx.author.mention}'s total bean vault value just **DOUBLED**!")
        else:
            if uid not in locked_vaults: player_beans[uid] = 0
            await ctx.send(f"🤮💀 **OVERDOSE!** The chemical compounds rejected {ctx.author.mention}. Their bank value has crashed down to **0**!")

    # 📢 ANONYMOUS PSA
    elif item_clean == "anonymous_psa":
        if not extra: return await ctx.send("❌ Include a broadcast message!")
        consume_item(uid, item_clean)
        await ctx.message.delete()
        await ctx.send(f"📢🗣️ **ANONYMOUS BROADCAST:** *\"{extra}\"*")

    # 📦 MYSTERY BOX / BOX OF TEMU TILES / 🎟️ TEMU VOUCHER
    elif item_clean in ["box_of_temu_tiles", "temu_voucher", "mystery_box"]:
        consume_item(uid, item_clean)
        reward = random.choice(list(SHOP_ITEMS.keys()))
        if uid not in player_inventories: player_inventories[uid] = []
        player_inventories[uid].append(reward)
        await ctx.send(f"🎟️🛍️ **MYSTERY RE-ROLL:** {ctx.author.mention} cashed in their cheap junk and unlocked: **{reward.replace('_', ' ').capitalize()}**!")

    # 🚨 BIG RED BUTTON
    elif item_clean == "big_red_button":
        consume_item(uid, item_clean)
        locked_vaults.clear()
        for k in player_beans.keys(): player_beans[k] = 10
        await ctx.send("🚨💥 **APOCALYPSE NOW!** Every single padlock exploded and all player assets have reset to **10 beans** flat!")

    # ✋ PALM READING
    elif item_clean == "palm_reading":
        if not target: return await ctx.send("❌ Tag a player to spy on!")
        consume_item(uid, item_clean)
        is_locked = "LOCKED 🔒" if target.id in locked_vaults else "UNPROTECTED 🔓"
        items = player_inventories.get(target.id, [])
        await ctx.send(f"✋🔮 **MYSTIC RESULTS:** {target.mention}'s vault is currently {is_locked}. Their stash contains: `{items}`.")

    # 👑 CROWN OF BEANS
    elif item_clean == "crown_of_beans":
        consume_item(uid, item_clean)
        crowned_players.add(uid)
        await ctx.send(f"👑🫘 **CORONATION:** {ctx.author.mention} put on the Crown of Beans!")

    # 🔒 PADLOCK
    elif item_clean == "padlock":
        consume_item(uid, item_clean)
        locked_vaults.add(uid)
        await ctx.send(f"🔒⚙️ **VAULT LOCKUP:** {ctx.author.mention} locked their vault!")

    # 🥄 WOODEN SPOON
    elif item_clean == "wooden_spoon":
        if not target: return await ctx.send("❌ Tag a player to hit!")
        consume_item(uid, item_clean)
        if uid in locked_vaults or target.id in locked_vaults:
            await ctx.send(f"🥄💥 **WHACK!** {ctx.author.mention} smacked {target.mention} and swiped exactly **2 beans**!")
            return
        player_beans[target.id] = max(0, player_beans.get(target.id, 0) - 2)
        player_beans[uid] = player_beans.get(uid, 0) + 2
        await ctx.send(f"🥄💥 **WHACK!** {ctx.author.mention} smacked {target.mention} and swiped exactly **2 beans**!")

    # 🛡️ MAGNUM CONDOM
    elif item_clean == "magnum_condom":
        consume_item(uid, item_clean)
        shielded_players.add(uid)
        await ctx.send(f"🛡️🎈 **BARRIER ENGAGED:** {ctx.author.mention} deployed a Magnum Shield.")

    # 📻 BOOMBOX
    elif item_clean == "boombox":
        if not target: return await ctx.send("❌ Tag a target to deafen!")
        consume_item(uid, item_clean)
        await ctx.send(f"📻🔊 **MAX VOLUME!** {ctx.author.mention} blasted heavy bass straight into {target.mention}'s ears.")


# =========================================================================
# 5. THE BEAN BAZAAR MARKET INTERFACE (100% PLAIN-TEXT SYSTEM)
# =========================================================================

@bot.command(name="shop")
async def show_shop(ctx):
    """Displays items inside the Bean Bazaar cleanly without any string translation bugs."""
    header = "✨🛒 **WELCOME TO THE BEAN BAZAAR** 🛒✨\n`All items are mystery-locked & non-refundable.`\n"
    table_text = "───────────────────────────────────────\n"
    
    for item, cost in SHOP_ITEMS.items():
        stock_count = SHOP_STOCK.get(item, 0)
        clean_name = item.replace("_", " ").capitalize()
        status_label = "Out of Stock" if stock_count <= 0 else f"Qty: {'Unlimited' if stock_count == 999 else stock_count}"
        
        table_text += f"{clean_name} ── {cost} bns ({status_label})\n"
        
    table_text += "───────────────────────────────────────\n"
    footer = "🛍️ **To purchase an item, use:** `!buy [item_name]`"
    await ctx.send(header + table_text + footer)


@bot.command(name="buy")
async def buy_item(ctx, item_name: str):
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    if item_clean not in SHOP_ITEMS:
        await ctx.send(f"❌ '{item_name}' isn't on the shelves!")
        return
        
    if SHOP_STOCK.get(item_clean, 0) <= 0:
        await ctx.send(f"🚫 **SOLD OUT!**")
        return
        
    if buyer_id not in player_inventories:
        player_inventories[buyer_id] = []
        
    if item_clean in player_inventories[buyer_id]:
        await ctx.send(f"🛑 **Inventory Bound!** You already have a copy! Max 1 per player.")
        return
        
    item_cost = SHOP_ITEMS[item_clean]
    current_balance = player_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🙅‍♂️ You can't afford that item. Costs `{item_cost} beans`.")
        return
        
    player_beans[buyer_id] -= item_cost
    player_inventories[buyer_id].append(item_clean)
    
    if SHOP_STOCK[item_clean] != 999:
        SHOP_STOCK[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🛍️ {ctx.author.mention} spent `{item_cost} beans` and pulled a **{clean_name}**! 💨")


# =========================================================================
# 6. SECONDARY SHOP EXCHANGES & COMBAT ENGINES
# =========================================================================

@bot.command(name="blackmarket")
async def show_secret_shop(ctx):
    header = "🕵️‍♂️🤫 **THE UNDERGROUND BLACK MARKET** 🤫🕵️‍♂️\n`Transactions are completely unrecorded.`\n"
    table_text = "```md\n"
    table_text += f"{'Secret Item':<20} | {'Price':<10} | {'Stock':<8}\n"
    table_text += "─" * 44 + "\n"
    
    for item, cost in SECRET_SHOP_ITEMS.items():
        stock_count = SECRET_SHOP_STOCK.get(item, 0)
        clean_name = item.replace("_", " ").capitalize()
        status_label = "DEPLETED" if stock_count <= 0 else f"Qty: {stock_count}"
        table_text += f"{clean_name:<20} | {cost:<10} bns | {status_label:<8}\n"
        
    table_text += "```\n"
    footer = "🛍️ **To buy from the shadows, use:** `!shadowbuy [item_name]`"
    await ctx.send(header + table_text + footer)


@bot.command(name="shadowbuy")
async def buy_secret_item(ctx, item_name: str):
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    if item_clean not in SECRET_SHOP_ITEMS:
        await ctx.send("❌ That item doesn't exist in the shadows.")
        return
        
    if SECRET_SHOP_STOCK.get(item_clean, 0) <= 0:
        await ctx.send("🚫 **DEPLETED!**")
        return
        
    if buyer_id not in player_inventories:
        player_inventories[buyer_id] = []
        
    if item_clean in player_inventories[buyer_id]:
        await ctx.send("🛑 You already have one of these items!")
        return
        
    item_cost = SECRET_SHOP_ITEMS[item_clean]
    current_balance = player_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🕵️‍♂️ *\"Come back when you're serious.\"*")
        return
        
    player_beans[buyer_id] -= item_cost
    player_inventories[buyer_id].append(item_clean)
    SECRET_SHOP_STOCK[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🤫 *An exchange is made in the dark.* {ctx.author.mention} smuggled out a **{clean_name}**! 💸")


@bot.command(name="use_salad")
async def use_salad(ctx, target1: discord.Member, target2: discord.Member, target3: discord.Member):
    buyer_id = ctx.author.id
    if not has_item(buyer_id, "3_bean_salad"):
        await ctx.send("❌ You don't have the **3 Bean Salad**!")
        return

    targets = [target1, target2, target3]
    if len(set(targets)) < 3 or buyer_id in [t.id for t in targets]:
        await ctx.send("❌ Three completely unique victims are required!")
        return

    consume_item(buyer_id, "3_bean_salad")
    await ctx.send("Salad bowl hurled! Parsing contamination fields...")
    
    reports = []
    for t in targets:
        if t.id in shielded_players:
            shielded_players.remove(t.id)
            reports.append(f"• {t.mention} deflected the blast using a `Magnum condom` shield!")
        else:
            reports.append(f"• {t.mention} got hit directly and is now fully infected with **Beanorrhea**!")
            
    await ctx.send(f"🥗☣️ **THE 3 BEAN SALAD ASSAULT:**\n" + "\n".join(reports))


@bot.command(name="game_over")
@commands.has_role("Bean Master")
async def terminate_match(ctx):
    if not player_beans:
        await ctx.send("🏁 **Game Over!** Zero data recorded!")
        return

    sorted_players = sorted(player_beans.items(), key=lambda item: item[1], reverse=True)
    divider_line = "─" * 35
    summary = f"🏁🏆 **THE MATCH HAS CONCLUDED!** 🏆🏁\n{divider_line}\n"
    
    for rank, (user_id, beans) in enumerate(sorted_players, start=1):
        try:
            member = await ctx.guild.fetch_member(user_id)
            mention_tag = member.mention
        except discord.NotFound:
            mention_tag = f"Rogue Soul (<@{user_id}>)"
            
        icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🔹")
        summary += f"{icon} {mention_tag} — `{beans} beans`\n"
        
    await ctx.send(summary + f"\n{divider_line}\nUntil next round... 🫘💥")


# --- ADMINISTRATIVE MASTER SHORTHANDS ---
@bot.command(name="add")
@commands.has_role("Bean Master")
async def quick_add(ctx, member: discord.Member, amount: int):
    player_beans[member.id] = player_beans.get(member.id, 0) + amount
    await ctx.send(f"🪙 **Added:** Transferred {amount} to {member.mention}!")


@bot.command(name="strip")
@commands.has_role("Bean Master")
async def quick_strip(ctx, member: discord.Member, amount: int):
    player_beans[member.id] = max(0, player_beans.get(member.id, 0) - amount)
    await ctx.send(f"🪓 **Stripped:** Confiscated {amount} from {member.mention}!")


@forage_beans.error
async def cooldown_logs(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait **{int(error.retry_after // 60)} minutes** before foraging again!")


bot.run(os.environ.get("DISCORD_TOKEN"))

