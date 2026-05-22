import os
import random
import discord
from discord.ext import commands

# Initialize bot configuration with message content capabilities
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SERVER-ISOLATED REGISTRIES ---
# Structure: { "server_id": { "user_id": value } }
player_beans = {}        # { server_id: { user_id: bean_count } }
player_inventories = {}  # { server_id: { user_id: ["item1", "item2"] } }

# --- SETS SEPARATED BY SERVER ---
# Structure: { "server_id": set([user_id1, user_id2]) }
locked_vaults = {}       # Tracks padlocks - SECRET FREEZER ENGAGED
crowned_players = {}     # Tracks crown protective shield
shielded_players = {}    # Tracks magnum protection
gmo_farmers = {}         # Tracks players with permanent forage multipliers

# --- THE BEAN BAZAAR STOCKS & PRICING ---
SHOP_ITEMS = {
    "compromised_note": 11,
    "paper_clip": 3,
    "suspicious_rock": 59,
    "bonus_beans": 5,
    "bean_swap": 102,
    "old_condom": 35,
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

# Track shop stock per server to prevent global sell-outs
# Structure: { "server_id": { "item_name": quantity } }
server_shop_stock = {}
server_blackmarket_stock = {}

# --- THE UNDERGROUND SECRET BLACK MARKET ---
SECRET_SHOP_ITEMS = {
    "skeleton_key": 150,
    "gmo_bean": 500,
    "counterfeit_coin": 75
}

# --- THE SECRET SAUCE: HELPER FUNCTIONS FOR SERVER ISOLATION ---

def get_server_dict(registry, guild_id):
    """Fetches the data dictionary for a specific server, creating it if missing."""
    g_id = str(guild_id)
    if g_id not in registry:
        registry[g_id] = {}
    return registry[g_id]

def get_server_stock(guild_id, secret=False):
    """Fetches or initializes stock counts explicitly isolated by server."""
    g_id = str(guild_id)
    if secret:
        if g_id not in server_blackmarket_stock:
            server_blackmarket_stock[g_id] = {k: 3 for k in SECRET_SHOP_ITEMS.keys()}
        return server_blackmarket_stock[g_id]
    else:
        if g_id not in server_shop_stock:
            server_shop_stock[g_id] = {k: 5 for k in SHOP_ITEMS.keys()}
        return server_shop_stock[g_id]

def check_server_set(server_set, guild_id, user_id):
    """Checks if a player has a status in this specific server."""
    g_id = str(guild_id)
    if g_id not in server_set:
        return False
    return user_id in server_set[g_id]

def add_to_server_set(server_set, guild_id, user_id):
    """Gives a player a status inside a specific server."""
    g_id = str(guild_id)
    if g_id not in server_set:
        server_set[g_id] = set()
    server_set[g_id].add(user_id)

def remove_from_server_set(server_set, guild_id, user_id):
    """Removes a player's status inside a specific server."""
    g_id = str(guild_id)
    if g_id in server_set and user_id in server_set[g_id]:
        server_set[g_id].remove(user_id)

def has_item(guild_id, user_id, item):
    """Checks if a player has an item in their server inventory."""
    server_inv = get_server_dict(player_inventories, guild_id)
    return user_id in server_inv and item in server_inv[user_id]

def consume_item(guild_id, user_id, item):
    """Consumes an item from a player's server-specific inventory."""
    server_inv = get_server_dict(player_inventories, guild_id)
    if user_id in server_inv and item in server_inv[user_id]:
        server_inv[user_id].remove(item)

async def check_shield(ctx, target):
    """Checks and consumes a magnum condom protective barrier."""
    if check_server_set(shielded_players, ctx.guild.id, target.id):
        remove_from_server_set(shielded_players, ctx.guild.id, target.id)
        await ctx.send(f"🛡️🛡️ **MAGNUM IMMUNITY!** {target.mention}'s Magnum Condom deflected the entire item deployment!")
        return True
    return False


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

        # Safeguard: Prevent Discord 2000 character limit crash
        victim_tags = " ".join([m.mention for m in mentions])
        if len(victim_tags) > 1500:
            await message.channel.send("❌ **Error:** Too many players tagged at once! Break them up into smaller groups.")
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

    # Process regular bot commands smoothly
    await bot.process_commands(message)


# =========================================================================
# 1. PLAYER UTILITY COMMANDS (!BEANBANK & !LEADERBOARD)
# =========================================================================

@bot.command(name="BeanBank")
async def check_bean_bank(ctx):
    player_id = ctx.author.id
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_inv = get_server_dict(player_inventories, ctx.guild.id)
    
    balance = server_beans.get(player_id, 0)
    inventory = server_inv.get(player_id, [])
    
    status = "🎒"
    if check_server_set(locked_vaults, ctx.guild.id, player_id): status = "🔒"
    if check_server_set(crowned_players, ctx.guild.id, player_id): status = "👑"
    
    bean_flavors = ["pinto beans", "magic beans", "jelly beans", "suspicious beans", "baked beans"]
    flavor = random.choice(bean_flavors)
    
    inv_text = ", ".join([f"`{i.replace('_', ' ').capitalize()}`" for i in inventory]) if inventory else "*Empty pockets...*"
    await ctx.send(f"🫘 {ctx.author.mention} has `{balance} {flavor}`\n{status} **Inventory Stash:** {inv_text}")


@bot.command(name="leaderboard")
async def show_leaderboard(ctx):
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    active_players = {k: v for k, v in server_beans.items() if v > 0}
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


# =========================================================================
# 2. ECONOMY ENGINES (FORAGE & STEAL with SECRET FREEZER)
# =========================================================================

@bot.command(name="forage")
@commands.cooldown(1, 3600, commands.BucketType.user)
async def forage_beans(ctx):
    player_id = ctx.author.id
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    
    if check_server_set(locked_vaults, ctx.guild.id, player_id):
        if random.randint(1, 100) <= 50:
            await ctx.send(f"🤢 **SOUR BEAN!** {ctx.author.mention} lost **{random.randint(5, 15)} beans** out of pure failure.")
        else:
            await ctx.send(f"🌳 **SURPRISE!** {ctx.author.mention} foraged **{random.randint(5, 15)} beans**! 🪙")
        return

    if random.randint(1, 100) <= 50:
        beans_lost = random.randint(5, 15)
        server_beans[player_id] = max(0, server_beans.get(player_id, 0) - beans_lost)
        await ctx.send(f"🤢 **SOUR BEAN!** {ctx.author.mention} lost **{beans_lost} beans** out of pure failure.")
        return
        
    beans_found = random.randint(5, 15)
    if check_server_set(gmo_farmers, ctx.guild.id, player_id):
        beans_found *= 2
    server_beans[player_id] = server_beans.get(player_id, 0) + beans_found
    await ctx.send(f"🌳 **SURPRISE!** {ctx.author.mention} foraged **{beans_found} beans**! 🪙")


@bot.command(name="steal")
async def steal_beans(ctx, target: discord.Member):
    if ctx.author.id == target.id: return
    thief_id, victim_id = ctx.author.id, target.id
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    
    if server_beans.get(victim_id, 0) <= 0:
        await ctx.send("🍂 Target has no beans!")
        return

    if check_server_set(locked_vaults, ctx.guild.id, victim_id):
        await ctx.send(f"🔒 **PADLOCK ACTIVE!** {ctx.author.mention} slammed face-first into {target.mention}'s lock!")
        return

    if check_server_set(crowned_players, ctx.guild.id, victim_id):
        remove_from_server_set(crowned_players, ctx.guild.id, victim_id)
        if check_server_set(locked_vaults, ctx.guild.id, thief_id):
            await ctx.send(f"👑💥 **CROWN COUNTER!** {target.mention}'s crown protected them! {ctx.author.mention} had to pay them **20 beans** in tribute!")
        else:
            server_beans[thief_id] = max(0, server_beans.get(thief_id, 0) - 20)
            server_beans[victim_id] = server_beans.get(victim_id, 0) + 20
            await ctx.send(f"👑💥 **CROWN COUNTER!** {target.mention}'s crown protected them! {ctx.author.mention} had to pay them **20 beans** in tribute!")
        return

    if check_server_set(locked_vaults, ctx.guild.id, thief_id):
        if random.randint(1, 100) <= 75:
            await ctx.send(f"🦊 **FAIL!** Gizmo intercepted {ctx.author.mention} and taxed them 10 beans.")
        else:
            victim_stash = server_beans.get(victim_id, 0)
            stolen_amount = random.randint(max(1, int(victim_stash * 0.1)), max(2, int(victim_stash * 0.3)))
            await ctx.send(f"🦝 **SUCCESS!** {ctx.author.mention} smoothly swiped **{stolen_amount} beans** from {target.mention}!")
        return

    if random.randint(1, 100) <= 75:
        server_beans[thief_id] = max(0, server_beans.get(thief_id, 0) - 10)
        await ctx.send(f"🦊 **FAIL!** Gizmo intercepted {ctx.author.mention} and taxed them 10 beans.")
        return
    
    victim_stash = server_beans.get(victim_id, 0)
    stolen_amount = random.randint(max(1, int(victim_stash * 0.1)), max(2, int(victim_stash * 0.3)))
    server_beans[victim_id] -= stolen_amount
    server_beans[thief_id] = server_beans.get(thief_id, 0) + stolen_amount
    await ctx.send(f"🦝 **SUCCESS!** {ctx.author.mention} smoothly swiped **{stolen_amount} beans** from {target.mention}!")


# =========================================================================
# 3. INTERACTIVE USE ENGINE FOR ALL ITEMS
# =========================================================================

@bot.command(name="use")
async def use_item_router(ctx, item_name: str, target: discord.Member = None, *, extra: str = ""):
    uid = ctx.author.id
    item_clean = item_name.strip().lower()
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_inv = get_server_dict(player_inventories, ctx.guild.id)

    if not has_item(ctx.guild.id, uid, item_clean):
        await ctx.send(f"❌ You don't have a `{item_clean}` in your stash!")
        return

    # 📝 COMPROMISED NOTE
    if item_clean == "compromised_note":
        if not target: return await ctx.send("❌ Tag a target to expose!")
        consume_item(ctx.guild.id, uid, item_clean)
        divider_line = "─" * 35
        await ctx.send(
            f"📝🚨 **COMPROMISED NOTE ACTIVATED!** 🚨📝\n{divider_line}\n"
            f"💥 {ctx.author.mention} has just cash-burned their Note to expose {target.mention}!\n\n"
            f"The paper trail has been handed directly over to the **Bean Masters**... \n"
            f"An executive judgment is being prepared in the shadows. Look alive. 👀"
        )

    # 📎 PAPER CLIP
    elif item_clean == "paper_clip":
        if not target: return await ctx.send("❌ Tag a player's vault to tamper with!")
        consume_item(ctx.guild.id, uid, item_clean)
        if check_server_set(locked_vaults, ctx.guild.id, uid):
            if random.randint(1, 100) <= 50: await ctx.send(f"📎🔒 **MESSY TAMPERING!** The clip snapped off in {target.mention}'s lock mechanism. Their vault is now permanently **LOCKED**!")
            else: await ctx.send(f"💥 **BOOM!** The clip triggered an anti-theft charge inside {target.mention}'s vault, vaporizing **15 beans**!")
            return
        if random.randint(1, 100) <= 50:
            add_to_server_set(locked_vaults, ctx.guild.id, target.id)
            await ctx.send(f"📎🔒 **MESSY TAMPERING!** The clip snapped off in {target.mention}'s lock mechanism. Their vault is now permanently **LOCKED**!")
        else:
            server_beans[target.id] = max(0, server_beans.get(target.id, 0) - 15)
            await ctx.send(f"💥 **BOOM!** The clip triggered an anti-theft charge inside {target.mention}'s vault, vaporizing **15 beans**!")

    # 🪨 SUSPICIOUS ROCK
    elif item_clean == "suspicious_rock":
        if not target: return await ctx.send("❌ Who are you throwing this rock at?")
        consume_item(ctx.guild.id, uid, item_clean)
        if await check_shield(ctx, target): return
        roll = random.randint(1, 100)
        if roll <= 40:
            await ctx.send(f"🥴 **BAMBOOZLED!** {target.mention} took a direct hit to the skull and must speak in gibberish!")
        elif roll <= 80:
            lost = random.randint(5, 20)
            if not check_server_set(locked_vaults, ctx.guild.id, target.id): 
                server_beans[target.id] = max(0, server_beans.get(target.id, 0) - lost)
            await ctx.send(f"💥💩 {target.mention} was startled so badly they dropped **{lost} beans** and shit themselves! This is worse than when Aunt Sally assploded in walmart and Gizmo was wrongfully banned!")
        else:
            if not check_server_set(locked_vaults, ctx.guild.id, uid): 
                server_beans[uid] = max(0, server_beans.get(uid, 0) - 10)
            await ctx.send(f"🦊 **GIZMO CATCH!** Gizmo caught the rock and hurled it back at {ctx.author.mention}, knocking out 10 beans!")

    # 🫘 BONUS BEANS
    elif item_clean == "bonus_beans":
        consume_item(ctx.guild.id, uid, item_clean)
        win = random.randint(1, 5)
        if not check_server_set(locked_vaults, ctx.guild.id, uid): 
            server_beans[uid] = server_beans.get(uid, 0) + win
        await ctx.send(f"🫘📈 **JACKPOT!** {ctx.author.mention} split open the seed pouch and claimed **{win} free beans**!")

    # 🔄 BEAN SWAP
    elif item_clean == "bean_swap":
        if not target: return await ctx.send("❌ Who are you swapping wealth with?")
        consume_item(ctx.guild.id, uid, item_clean)
        if check_server_set(locked_vaults, ctx.guild.id, uid) or check_server_set(locked_vaults, ctx.guild.id, target.id):
            await ctx.send(f"🔄🔮 **THE BALANCE FLIP!** {ctx.author.mention} and {target.mention} just completely swapped bank balances!")
            return
        my_beans = server_beans.get(uid, 0)
        their_beans = server_beans.get(target.id, 0)
        server_beans[uid], server_beans[target.id] = their_beans, my_beans
        await ctx.send(f"🔄🔮 **THE BALANCE FLIP!** {ctx.author.mention} and {target.mention} just completely swapped bank balances!")

    # 🎈 OLD CONDOM
    elif item_clean == "old_condom":
        if not target: return await ctx.send("❌ Tag a target to snap!")
        consume_item(ctx.guild.id, uid, item_clean)
        if random.randint(1, 100) <= 50:
            if not check_server_set(locked_vaults, ctx.guild.id, target.id): 
                server_beans[target.id] = max(0, server_beans.get(target.id, 0) - 5)
            await ctx.send(f"🎈💥 **SNAP!** An old balloon hit {target.mention} square in the eyes. They lost 5 beans!")
        else:
            if not check_server_set(locked_vaults, ctx.guild.id, uid): 
                server_beans[uid] = max(0, server_beans.get(uid, 0) - 5)
            await ctx.send(f"💥🤦‍♂️ **BACKFIRE!** The material snapped backward hitting {ctx.author.mention} instead! Lost 5 beans.")

    # 🦆 CRUSTY RUBBER DUCK
    elif item_clean == "crusty_rubber_duck":
        consume_item(ctx.guild.id, uid, item_clean)
        await ctx.send("🦆💤 *SQUEAK!* The crusty duck echoes across the layout...")
        keys = list(server_beans.keys())
        if len(keys) >= 3:
            targets = random.sample(keys, 3)
            for t in targets: 
                if not check_server_set(locked_vaults, ctx.guild.id, t): 
                    server_beans[t] = max(0, server_beans.get(t, 0) + random.choice([-5, 5]))
            await ctx.send("🦊 **GIZMO CHAOS:** Gizmo ran wild and modified the balances of 3 random participants!")

    # 🥗 3 BEAN SALAD
    elif item_clean == "3_bean_salad":
        await ctx.send("❌ Please handle the legendary biowarfare salad explicitly using the dedicated layout command: `!use_salad @P1 @P2 @P3`")

    # 💊 STRANGE PILL
    elif item_clean == "strange_pill":
        consume_item(ctx.guild.id, uid, item_clean)
        if random.randint(1, 100) <= 50:
            if not check_server_set(locked_vaults, ctx.guild.id, uid): 
                server_beans[uid] *= 2
            await ctx.send(f"💊⚡ **CRITICAL SURGE!** {ctx.author.mention}'s total bean vault value just **DOUBLED**!")
        else:
            if not check_server_set(locked_vaults, ctx.guild.id, uid): 
                server_beans[uid] = 0
            await ctx.send(f"🤮💀 **OVERDOSE!** The chemical compounds rejected {ctx.author.mention}. Their bank value has crashed down to **0**!")

    # 📢 ANONYMOUS PSA
    elif item_clean == "anonymous_psa":
        if not extra: return await ctx.send("❌ Include a broadcast message!")
        consume_item(ctx.guild.id, uid, item_clean)
        await ctx.message.delete()
        await ctx.send(f"📢🗣️ **ANONYMOUS BROADCAST:** *\"{extra}\"*")

    # 📦 BOX OF TEMU TILES / 🎟️ TEMU VOUCHER
    elif item_clean in ["box_of_temu_tiles", "temu_voucher"]:
        consume_item(ctx.guild.id, uid, item_clean)
        reward = random.choice(list(SHOP_ITEMS.keys()))
        if uid not in server_inv: server_inv[uid] = []
        server_inv[uid].append(reward)
        await ctx.send(f"🎟️🛍️ **TEMU RE-ROLL:** {ctx.author.mention} cashed in their cheap junk and unlocked: **{reward.replace('_', ' ').capitalize()}**!")

    # 🚨 BIG RED BUTTON
    elif item_clean == "big_red_button":
        consume_item(ctx.guild.id, uid, item_clean)
        if ctx.guild.id in locked_vaults:
            locked_vaults[ctx.guild.id].clear()
        for k in server_beans.keys(): server_beans[k] = 10
        await ctx.send("🚨💥 **APOCALYPSE NOW!** The big red button was smashed down. Every single padlock exploded and all player assets have reset to **10 beans** flat!")

    # ✋ PALM READING
    elif item_clean == "palm_reading":
        if not target: return await ctx.send("❌ Tag a player to spy on!")
        consume_item(ctx.guild.id, uid, item_clean)
        is_locked = "LOCKED 🔒" if check_server_set(locked_vaults, ctx.guild.id, target.id) else "UNPROTECTED 🔓"
        items = server_inv.get(target.id, [])
        await ctx.send(f"✋🔮 **MYSTIC RESULTS:** {target.mention}'s vault is currently {is_locked}. Their stash contains: `{items}`.")

    # 👑 CROWN OF BEANS
    elif item_clean == "crown_of_beans":
        consume_item(ctx.guild.id, uid, item_clean)
        add_to_server_set(crowned_players, ctx.guild.id, uid)
        await ctx.send(f"👑🫘 **CORONATION:** {ctx.author.mention} put on the Crown of Beans! The next thief to cross them will face severe taxes.")

    # 🔒 PADLOCK
    elif item_clean == "padlock":
        consume_item(ctx.guild.id, uid, item_clean)
        add_to_server_set(locked_vaults, ctx.guild.id, uid)
        await ctx.send(f"🔒⚙️ **VAULT LOCKUP:** {ctx.author.mention} locked their vault, making them totally immune to baseline theft!")

    # 🥄 WOODEN SPOON
    elif item_clean == "wooden_spoon":
        if not target: return await ctx.send("❌ Tag a player to hit!")
        consume_item(ctx.guild.id, uid, item_clean)
        if check_server_set(locked_vaults, ctx.guild.id, uid) or check_server_set(locked_vaults, ctx.guild.id, target.id):
            await ctx.send(f"🥄💥 **WHACK!** {ctx.author.mention} smacked {target.mention} across the knees with a wooden spoon and swiped exactly **2 beans**!")
            return
        server_beans[target.id] = max(0, server_beans.get(target.id, 0) - 2)
        server_beans[uid] = server_beans.get(uid, 0) + 2
        await ctx.send(f"🥄💥 **WHACK!** {ctx.author.mention} smacked {target.mention} across the knees with a wooden spoon and swiped exactly **2 beans**!")

    # 🛡️ MAGNUM CONDOM
    elif item_clean == "magnum_condom":
        consume_item(ctx.guild.id, uid, item_clean)
        add_to_server_set(shielded_players, ctx.guild.id, uid)
        await ctx.send(f"🛡️🎈 **BARRIER ENGAGED:** {ctx.author.mention} deployed a Magnum Shield. They are immune to the next incoming offensive item!")

    # 📻 BOOMBOX
    elif item_clean == "boombox":
        if not target: return await ctx.send("❌ Tag a target to deafen!")
        consume_item(ctx.guild.id, uid, item_clean)
        await ctx.send(f"📻🔊 **MAX VOLUME!** {ctx.author.mention} blasted heavy bass straight into {target.mention}'s ears. They are totally disoriented!")

    # 🔑 SECRET SKELETON KEY
    elif item_clean == "skeleton_key":
        consume_item(ctx.guild.id, uid, item_clean)
        if check_server_set(locked_vaults, ctx.guild.id, uid):
            remove_from_server_set(locked_vaults, ctx.guild.id, uid)
            await ctx.send(f"🔓⚙️ **LOCK SHATTERED!** {ctx.author.mention} forced a Skeleton Key into their padlock! The lock snaps in half—their vault is **UNFROZEN** and fully open for business!")
        else:
            await ctx.send(f"🔑 {ctx.author.mention} turned the skeleton key in an empty lock. It clicks pointlessly, but the key is consumed anyway.")

    # 🫘🧬 SECRET GMO BEAN
    elif item_clean == "gmo_bean":
        consume_item(ctx.guild.id, uid, item_clean)
        add_to_server_set(gmo_farmers, ctx.guild.id, uid)
        await ctx.send(f"🧬🫘 **GENETIC MODIFICATION:** {ctx.author.mention} swallowed a glowing GMO Bean! Their future forage rewards are now permanently **DOUBLED**!")

    # 🪙❌ SECRET COUNTERFEIT COIN
    elif item_clean == "counterfeit_coin":
        if not target: return await ctx.send("❌ Tag a target to frame!")
        consume_item(ctx.guild.id, uid, item_clean)
        if await check_shield(ctx, target): return
        if not check_server_set(locked_vaults, ctx.guild.id, target.id):
            server_beans[target.id] = max(0, server_beans.get(target.id, 0) - 50)
        await ctx.send(f"🚨👮‍♂️ **FRAUD DETECTED!** Anti-counterfeiting guards caught {target.mention} spending illegal tokens! The bank has confiscated **50 beans** from their stash as punishment!")


# =========================================================================
# 4. THE BEAN BAZAAR MARKET INTERFACE (PSEUDO-CURSIVE RENDERING)
# =========================================================================

@bot.command(name="shop")
async def show_shop(ctx):
    """Displays items inside the Bean Bazaar using a stylized cursive layout."""
    cursive_map = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫"
    )
    
    header = "✨🛒 **𝒲ℯ𝓁𝒸ℴ𝓂ℯ 𝓉ℴ 𝓉𝒽ℯ ℬℯ𝒶𝓃 ℬ𝒶𝓏𝒶𝒶𝓇** 🛒✨\n`All items are mystery-locked & non-refundable.`\n"
    table_text = "───────────────────────────────────────\n"
    
    stock = get_server_stock(ctx.guild.id)
    for item, cost in SHOP_ITEMS.items():
        stock_count = stock.get(item, 5)
        clean_name = item.replace("_", " ").capitalize()
        status_label = "𝒪𝓊𝓉 ℴ𝒻 𝒮𝓉ℴ𝒸𝓀" if stock_count <= 0 else f"𝒬𝓉𝓎: {stock_count}"
        
        raw_row = f"{clean_name} ── {cost} bns ({status_label})\n"
        table_text += raw_row.translate(cursive_map)
        
    table_text += "───────────────────────────────────────\n"
    footer = "🛍️ **To purchase an item, use:** `!buy [item_name]`"
    
    await ctx.send(header + table_text + footer)


@bot.command(name="buy")
async def buy_item(ctx, item_name: str):
    """Processes item purchases securely and updates stock layouts."""
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_inv = get_server_dict(player_inventories, ctx.guild.id)
    stock = get_server_stock(ctx.guild.id)
    
    if item_clean not in SHOP_ITEMS:
        await ctx.send(f"❌ '{item_name}' isn't on the shelves! Check spelling or view the book via `!shop`.")
        return
        
    if stock.get(item_clean, 0) <= 0:
        await ctx.send(f"🚫 **SOLD OUT!** The supply of **{item_clean.replace('_', ' ').capitalize()}** is gone!")
        return
        
    if buyer_id not in server_inv:
        server_inv[buyer_id] = []
        
    if item_clean in server_inv[buyer_id]:
        await ctx.send(f"🛑 **Inventory Bound!** You already have a copy of this item! Max 1 per player.")
        return
        
    item_cost = SHOP_ITEMS[item_clean]
    current_balance = server_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🙅‍♂️ You can't afford that item. Costs `{item_cost} beans`, but you only have `{current_balance}`.")
        return
        
    server_beans[buyer_id] -= item_cost
    server_inv[buyer_id].append(item_clean)
    stock[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🛍️ {ctx.author.mention} spent `{item_cost} beans` and pulled a **{clean_name}**! 💨")


@bot.command(name="blackmarket")
async def show_secret_shop(ctx):
    """The underground hidden black market text grid."""
    header = "🕵️‍♂️🤫 **THE UNDERGROUND BLACK MARKET** 🤫🕵️‍♂️\n`You shouldn't be here. Transactions are completely unrecorded.`\n"
    
    table_text = "```md\n"
    table_text += f"{'Secret Item':<20} | {'Price':<10} | {'Stock':<8}\n"
    table_text += "─" * 44 + "\n"
    
    stock = get_server_stock(ctx.guild.id, secret=True)
    for item, cost in SECRET_SHOP_ITEMS.items():
        stock_count = stock.get(item, 3)
        clean_name = item.replace("_", " ").capitalize()
        
        status_label = "DEPLETED" if stock_count <= 0 else f"Qty: {stock_count}"
        cost_label = f"{cost} bns"
        table_text += f"{clean_name:<20} | {cost_label:<10} | {status_label:<8}\n"
        
    table_text += "```\n"
    footer = "🛍️ **To buy from the shadows, use:** `!shadowbuy [item_name]`"
    await ctx.send(header + table_text + footer)


@bot.command(name="shadowbuy")
async def buy_secret_item(ctx, item_name: str):
    """Processes confidential underground black market purchases."""
    buyer_id = ctx.author.id
    item_clean = item_name.strip().lower()
    
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_inv = get_server_dict(player_inventories, ctx.guild.id)
    stock = get_server_stock(ctx.guild.id, secret=True)
    
    if item_clean not in SECRET_SHOP_ITEMS:
        await ctx.send("❌ That item doesn't exist in the shadows... watch your step.")
        return
        
    if stock.get(item_clean, 0) <= 0:
        await ctx.send("🚫 **DEPLETED!** The black market supplier has gone dark on this item.")
        return
        
    if buyer_id not in server_inv:
        server_inv[buyer_id] = []
        
    if item_clean in server_inv[buyer_id]:
        await ctx.send("🛑 You already have one of these smuggled items in your jacket pocket!")
        return
        
    item_cost = SECRET_SHOP_ITEMS[item_clean]
    current_balance = server_beans.get(buyer_id, 0)
    
    if current_balance < item_cost:
        await ctx.send(f"🕵️‍♂️ *\"Come back when you're serious.\"* (Costs `{item_cost} beans`, you only have `{current_balance}`).")
        return
        
    server_beans[buyer_id] -= item_cost
    server_inv[buyer_id].append(item_clean)
    stock[item_clean] -= 1
    
    clean_name = item_clean.replace('_', ' ').capitalize()
    await ctx.send(f"🤫 *An exchange is made in the dark.* {ctx.author.mention} smuggled out a **{clean_name}**! 💸")


# =========================================================================
# 5. EXPLICIT 3 BEAN SALAD ENGINE
# =========================================================================

@bot.command(name="use_salad")
async def use_salad(ctx, target1: discord.Member, target2: discord.Member, target3: discord.Member):
    buyer_id = ctx.author.id
    if not has_item(ctx.guild.id, buyer_id, "3_bean_salad"):
        await ctx.send("❌ You don't have the **3 Bean Salad**!")
        return

    targets = [target1, target2, target3]
    if len(set(targets)) < 3 or buyer_id in [t.id for t in targets]:
        await ctx.send("❌ Three completely unique victims are required!")
        return

    consume_item(ctx.guild.id, buyer_id, "3_bean_salad")
    await ctx.send("Salad bowl hurled! Parsing contamination fields...")
    
    reports = []
    for t in targets:
        if check_server_set(shielded_players, ctx.guild.id, t.id):
            remove_from_server_set(shielded_players, ctx.guild.id, t.id)
            reports.append(f"• {t.mention} deflected the blast using a `Magnum condom` shield!")
        else:
            reports.append(f"• {t.mention} got hit directly and is now fully infected with **Beanorrhea**!")
            
    await ctx.send(f"🥗☣️ **THE 3 BEAN SALAD ASSAULT:**\n" + "\n".join(reports))


# =========================================================================
# 6. MATCH ENDGAME AGGREGATOR
# =========================================================================

@bot.command(name="game_over")
@commands.has_role("Bean Master")
async def terminate_match(ctx):
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    if not server_beans:
        await ctx.send("🏁 **Game Over!** Zero data recorded!")
        return

    sorted_players = sorted(server_beans.items(), key=lambda item: item[1], reverse=True)
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
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_beans[member.id] = server_beans.get(member.id, 0) + amount
    await ctx.send(f"🪙 **Added:** Transferred {amount} to {member.mention}!")


@bot.command(name="strip")
@commands.has_role("Bean Master")
async def quick_strip(ctx, member: discord.Member, amount: int):
    server_beans = get_server_dict(player_beans, ctx.guild.id)
    server_beans[member.id] = max(0, server_beans.get(member.id, 0) - amount)
    await ctx.send(f"🪓 **Stripped:** Confiscated {amount} from {member.mention}!")


# --- ERROR PROTECTION COOLDOWNS ---
@forage_beans.error
async def cooldown_logs(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait **{int(error.retry_after // 60)} minutes** before foraging again!")


bot.run(os.environ.get("DISCORD_TOKEN"))
