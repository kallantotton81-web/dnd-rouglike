// --- Constants ---
const TILE_SIZE = 20;
const FOV_RADIUS = 8;
const MAX_FLOORS = 20;

const COLORS = {
    VOID: '#0a0a0e',
    WALL: '#646464',
    WALL_DARK: '#323232',
    FLOOR: '#1a1a1a',
    HEALTH: '#ff4b2b',
    GOLD: '#ffd700',
    CYAN: '#00ffff',
    WHITE: '#e0e0e0'
};

// --- Helper Classes ---
class Rect {
    constructor(x, y, w, h) {
        this.x1 = x; this.y1 = y;
        this.x2 = x + w; this.y2 = y + h;
    }
    center() {
        return { x: Math.floor((this.x1 + this.x2) / 2), y: Math.floor((this.y1 + this.y2) / 2) };
    }
    intersect(other) {
        return (this.x1 <= other.x2 && this.x2 >= other.x1 && this.y1 <= other.y2 && this.y2 >= other.y1);
    }
}

class Tile {
    constructor(blocked, blockSight = null) {
        this.blocked = blocked;
        this.blockSight = blockSight === null ? blocked : blockSight;
        this.visible = false;
        this.explored = false;
    }
}

// --- Entity Component System ---
class Entity {
    constructor(x, y, name, char, color, props = {}) {
        this.x = x; this.y = y;
        this.name = name; this.char = char; this.color = color;
        this.blocksMovement = props.blocksMovement || false;
        this.fighter = props.fighter || null;
        this.item = props.item || null;
        this.equippable = props.equippable || null;
        this.stairs = props.stairs || false;
    }
}

class Fighter {
    constructor(hp, ac, stats, lives = 1) {
        this.maxHp = hp; this.hp = hp;
        this.ac = ac; this.stats = stats;
        this.lives = lives;
        this.gold = 0; this.level = 1; this.xp = 0;
        this.weapon = null; this.armor = null; this.scroll = null;
    }
}

class ItemComp {
    constructor(useFunc, props = {}) {
        this.useFunc = useFunc;
        this.isIdentified = props.isIdentified !== undefined ? props.isIdentified : true;
        this.spell = props.spell || null;
        this.amount = props.amount || 0;
        this.charges = props.charges || null;
    }
}

// --- Spells ---
const Spells = {
    MagicMissile: {
        name: "Magic Missile", range: 5, cast: (engine, target) => {
            const dmg = Math.floor(Math.random() * 4) + 1 + 2;
            target.fighter.hp -= dmg;
            return `Magic Missile hits ${target.name} for ${dmg} damage!`;
        }
    },
    Fireball: {
        name: "Fireball", range: 4, cast: (engine, target) => {
            const dmg = Math.floor(Math.random() * 8) + 1 + 4;
            target.fighter.hp -= dmg;
            return `Fireball engulfs ${target.name} for ${dmg} fire damage!`;
        }
    }
};

// --- Engine ---
class GameEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.currentFloor = 1;
        this.entities = [];
        this.player = null;
        this.map = [];
        this.mapWidth = 25;
        this.mapHeight = 18;
    }

    start(charClass) {
        this.setupPlayer(charClass);
        this.newFloor();
        this.updateHUD();
        this.render();
        window.addEventListener('keydown', (e) => this.handleInput(e));
    }

    setupPlayer(className) {
        let stats = { str: 10, dex: 10, con: 10 };
        let hp = 20, ac = 10;

        if (className === 'Fighter') { stats.str = 16; stats.con = 14; hp = 30; }
        else if (className === 'Wizard') { stats.str = 8; stats.dex = 14; hp = 15; }
        else if (className === 'Rogue') { stats.dex = 18; ac = 14; hp = 20; }

        this.player = new Entity(0, 0, 'Player', '@', COLORS.WHITE, {
            fighter: new Fighter(hp, ac, stats, 3)
        });
        this.player.className = className;
        this.player.startingSpell = className === 'Wizard' ? Spells.MagicMissile : null;
    }

    newFloor() {
        if (this.currentFloor > MAX_FLOORS) {
            document.getElementById('victory-screen').classList.remove('hidden');
            return;
        }

        // Scaling code
        this.mapWidth = Math.min(45, 25 + (this.currentFloor - 1) * 2);
        this.mapHeight = Math.min(35, 18 + (this.currentFloor - 1));
        const maxRooms = Math.min(25, 10 + (this.currentFloor - 1));

        this.generateMap(this.mapWidth, this.mapHeight, maxRooms);
        this.addMessage(`Floor ${this.currentFloor} - Good luck.`, COLORS.GOLD);
        this.computeFOV();
    }

    generateMap(width, height, maxRooms) {
        this.map = Array.from({ length: width }, () => Array.from({ length: height }, () => new Tile(true)));
        this.entities = [this.player];

        let rooms = [];
        for (let r = 0; r < maxRooms; r++) {
            let w = Math.floor(Math.random() * 5) + 4;
            let h = Math.floor(Math.random() * 5) + 4;
            let x = Math.floor(Math.random() * (width - w - 1));
            let y = Math.floor(Math.random() * (height - h - 1));

            let newRoom = new Rect(x, y, w, h);
            if (!rooms.some(other => newRoom.intersect(other))) {
                this.digRoom(newRoom);
                let center = newRoom.center();
                if (rooms.length === 0) {
                    this.player.x = center.x; this.player.y = center.y;
                } else {
                    let prev = rooms[rooms.length - 1].center();
                    this.digTunnel(prev.x, prev.y, center.x, center.y);
                    this.spawnRoomContent(newRoom);
                }
                rooms.push(newRoom);
            }
        }

        // Spawn Stairs in last room
        const lastRoom = rooms[rooms.length - 1].center();
        this.entities.push(new Entity(lastRoom.x, lastRoom.y, 'Stairs', '>', COLORS.GOLD, { stairs: true }));
    }

    digRoom(room) {
        for (let x = room.x1 + 1; x < room.x2; x++) {
            for (let y = room.y1 + 1; y < room.y2; y++) {
                this.map[x][y].blocked = false; this.map[x][y].blockSight = false;
            }
        }
    }

    digTunnel(x1, y1, x2, y2) {
        let x = x1, y = y1;
        while (x !== x2) {
            this.map[x][y].blocked = false; this.map[x][y].blockSight = false;
            x += x < x2 ? 1 : -1;
        }
        while (y !== y2) {
            this.map[x][y].blocked = false; this.map[x][y].blockSight = false;
            y += y < y2 ? 1 : -1;
        }
    }

    spawnRoomContent(room) {
        // Simple monster spawn
        if (Math.random() < 0.5) {
            let x = room.x1 + 1 + Math.floor(Math.random() * (room.x2 - room.x1 - 1));
            let y = room.y1 + 1 + Math.floor(Math.random() * (room.y2 - room.y1 - 1));
            if (!this.entities.some(e => e.x === x && e.y === y)) {
                this.entities.push(new Entity(x, y, 'Orc', 'o', COLORS.HEALTH, {
                    blocksMovement: true,
                    fighter: new Fighter(10, 12, { str: 12, dex: 10, con: 10 })
                }));
            }
        }
        // Spawn Scroll
        if (Math.random() < 0.3) {
            let x = room.x1 + 1 + Math.floor(Math.random() * (room.x2 - room.x1 - 1));
            let y = room.y1 + 1 + Math.floor(Math.random() * (room.y2 - room.y1 - 1));
            const spell = Math.random() < 0.5 ? Spells.MagicMissile : Spells.Fireball;
            this.entities.push(new Entity(x, y, `Scroll of ${spell.name}`, '?', COLORS.CYAN, {
                item: new ItemComp(this.useScroll.bind(this), { isIdentified: false, spell: spell }),
                equippable: { slot: 'scroll' }
            }));
        }

        // Spawn Weapon
        if (Math.random() < 0.2) {
            let x = room.x1 + 1 + Math.floor(Math.random() * (room.x2 - room.x1 - 1));
            let y = room.y1 + 1 + Math.floor(Math.random() * (room.y2 - room.y1 - 1));
            const r = Math.random();
            let name, char, color, dice, sides;

            if (r < 0.05) {
                name = "Excalibur"; char = "/"; color = COLORS.GOLD; dice = 2; sides = 20;
            } else if (r < 0.5) {
                name = "Longsword"; char = "/"; color = COLORS.WHITE; dice = 1; sides = 8;
            } else {
                name = "Dagger"; char = "/"; color = COLORS.WHITE; dice = 1; sides = 4;
            }

            this.entities.push(new Entity(x, y, name, char, color, {
                item: new ItemComp(null, { dice, sides }),
                equippable: { slot: 'weapon' }
            }));
        }
    }

    useScroll(itemEnt) {
        const item = itemEnt.item;
        const monsters = this.entities.filter(e => e.fighter && e !== this.player);
        if (monsters.length === 0) return "No monsters in sight.";

        const target = monsters.reduce((n, m) =>
            this.dist(m, this.player) < this.dist(n, this.player) ? m : n
        );

        if (this.dist(target, this.player) > item.spell.range) return "Target too far!";

        const msg = `You read the ${itemEnt.name}. ` + item.spell.cast(this, target);
        item.isIdentified = true;
        this.player.inventory = this.player.inventory.filter(i => i !== itemEnt);
        if (this.player.fighter.scroll === itemEnt) this.player.fighter.scroll = null;
        this.checkDeath(target);
        return msg;
    }

    dist(a, b) { return Math.abs(a.x - b.x) + Math.abs(a.y - b.y); }

    handleInput(e) {
        let dx = 0, dy = 0;
        switch (e.key.toLowerCase()) {
            case 'w': case 'arrowup': dy = -1; break;
            case 's': case 'arrowdown': dy = 1; break;
            case 'a': case 'arrowleft': dx = -1; break;
            case 'd': case 'arrowright': dx = 1; break;
            case 'g': this.pickup(); break;
            case 'c': this.castActive(); break;
            case 'enter': this.stairsCheck(); break;
        }
        if (dx !== 0 || dy !== 0) this.move(dx, dy);
    }

    move(dx, dy) {
        const destX = this.player.x + dx;
        const destY = this.player.y + dy;
        const target = this.entities.find(e => e.x === destX && e.y === destY && e.fighter);

        if (target) this.attack(this.player, target);
        else if (destX >= 0 && destX < this.mapWidth && destY >= 0 && destY < this.mapHeight && !this.map[destX][destY].blocked) {
            this.player.x = destX; this.player.y = destY;
        }
        this.monsterTurn();
        this.computeFOV();
        this.updateHUD();
        this.render();
    }

    attack(attacker, target) {
        let dice = 1, sides = 6; // Default unarmed
        if (attacker.fighter.weapon) {
            dice = attacker.fighter.weapon.item.dice || 1;
            sides = attacker.fighter.weapon.item.sides || 6;
        }

        let dmg = 0;
        for (let i = 0; i < dice; i++) dmg += Math.floor(Math.random() * sides) + 1;

        // Add strength bonus (simplified)
        const strBonus = Math.floor((attacker.fighter.stats.str - 10) / 2);
        dmg += Math.max(0, strBonus);

        target.fighter.hp -= dmg;
        this.addMessage(`${attacker.name} hits ${target.name} for ${dmg}!`);
        this.checkDeath(target);
    }

    checkDeath(entity) {
        if (entity.fighter.hp <= 0) {
            if (entity === this.player) {
                this.player.fighter.lives--;
                if (this.player.fighter.lives > 0) {
                    this.addMessage("YOU DIED! Resurrecting...", COLORS.HEALTH);
                    this.player.fighter.hp = this.player.fighter.maxHp;
                } else {
                    document.getElementById('game-over-screen').classList.remove('hidden');
                }
            } else {
                this.addMessage(`${entity.name} falls!`);
                this.entities = this.entities.filter(e => e !== entity);
            }
        }
    }

    pickup() {
        const itemEnt = this.entities.find(e => e.x === this.player.x && e.y === this.player.y && e.item);
        if (itemEnt) {
            this.player.inventory = this.player.inventory || [];
            this.player.inventory.push(itemEnt);
            this.entities = this.entities.filter(e => e !== itemEnt);
            this.addMessage(`Picked up ${itemEnt.name}.`);
            this.updateInventoryUI();
            this.monsterTurn();
            this.render();
        }
    }

    castActive() {
        const scroll = this.player.fighter.scroll;
        if (scroll) {
            this.addMessage(this.useScroll(scroll));
            this.updateInventoryUI();
            this.monsterTurn();
            this.render();
        } else if (this.player.startingSpell) {
            const monsters = this.entities.filter(e => e.fighter && e !== this.player);
            if (monsters.length > 0) {
                const target = monsters[0]; // Nearest check would be better
                this.addMessage(this.player.startingSpell.cast(this, target));
                this.checkDeath(target);
                this.monsterTurn();
                this.render();
            }
        } else {
            this.addMessage("No active spell!");
        }
    }

    stairsCheck() {
        const stairs = this.entities.find(e => e.x === this.player.x && e.y === this.player.y && e.stairs);
        if (stairs) {
            this.currentFloor++;
            this.newFloor();
            this.render();
        }
    }

    monsterTurn() {
        this.entities.filter(e => e.fighter && e !== this.player).forEach(m => {
            const distance = this.dist(m, this.player);

            if (distance === 1) {
                // Adjacent: Attack
                this.attack(m, this.player);
            } else if (distance <= 8) {
                // Close enough: Move towards player
                let dx = 0, dy = 0;
                if (m.x < this.player.x) dx = 1; else if (m.x > this.player.x) dx = -1;
                if (m.y < this.player.y) dy = 1; else if (m.y > this.player.y) dy = -1;

                if (dx !== 0 || dy !== 0) {
                    // Try moving in x, then y (simple pathfinding)
                    let tx = m.x + dx, ty = m.y;
                    if (!this.map[tx][ty].blocked && !this.entities.some(e => e.x === tx && e.y === ty && e.blocksMovement)) {
                        m.x = tx; m.y = ty;
                    } else {
                        tx = m.x; ty = m.y + dy;
                        if (!this.map[tx][ty].blocked && !this.entities.some(e => e.x === tx && e.y === ty && e.blocksMovement)) {
                            m.x = tx; m.y = ty;
                        }
                    }
                }
            }
        });
    }

    // --- Rendering & UI ---
    computeFOV() {
        this.map.forEach(col => col.forEach(t => t.visible = false));
        for (let i = 0; i < 360; i += 5) {
            let rad = i * Math.PI / 180;
            for (let r = 0; r < FOV_RADIUS; r++) {
                let x = Math.round(this.player.x + Math.cos(rad) * r);
                let y = Math.round(this.player.y + Math.sin(rad) * r);
                if (x >= 0 && x < this.mapWidth && y >= 0 && y < this.mapHeight) {
                    this.map[x][y].visible = true; this.map[x][y].explored = true;
                    if (this.map[x][y].blockSight) break;
                }
            }
        }
    }

    render() {
        this.ctx.fillStyle = COLORS.VOID;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.font = `${TILE_SIZE - 2}px monospace`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        for (let x = 0; x < this.mapWidth; x++) {
            for (let y = 0; y < this.mapHeight; y++) {
                let t = this.map[x][y];
                if (!t.explored) continue;
                this.ctx.fillStyle = t.visible ? COLORS.FLOOR : '#050505';
                this.ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                if (t.blocked) {
                    this.ctx.fillStyle = t.visible ? COLORS.WALL : COLORS.WALL_DARK;
                    this.ctx.fillText('#', x * TILE_SIZE + 10, y * TILE_SIZE + 10);
                }
            }
        }

        this.entities.forEach(e => {
            if (this.map[e.x][e.y].visible) {
                this.ctx.fillStyle = e.color;
                this.ctx.fillText(e.char, e.x * TILE_SIZE + 10, e.y * TILE_SIZE + 10);
            }
        });
    }

    updateHUD() {
        const f = this.player.fighter;
        const hpPct = (f.hp / f.maxHp) * 100;
        document.getElementById('hp-bar').style.width = `${hpPct}%`;
        document.getElementById('hp-text').innerText = `HP: ${f.hp} / ${f.maxHp}`;
        document.getElementById('lives-count').innerText = f.lives;
        document.getElementById('floor-num').innerText = this.currentFloor;

        let spellText = "None";
        if (f.scroll) spellText = f.scroll.item.isIdentified ? f.scroll.name : "Unknown Scroll";
        else if (this.player.startingSpell) spellText = this.player.startingSpell.name;
        document.getElementById('active-spell').innerText = spellText;
    }

    updateInventoryUI() {
        const list = document.getElementById('inventory-list');
        list.innerHTML = '';
        (this.player.inventory || []).forEach(itemEnt => {
            const li = document.createElement('li');
            li.innerText = itemEnt.item.isIdentified ? itemEnt.name : "? (Unknown)";
            li.onclick = () => {
                if (itemEnt.equippable) {
                    if (itemEnt.equippable.slot === 'scroll') {
                        this.player.fighter.scroll = (this.player.fighter.scroll === itemEnt) ? null : itemEnt;
                        this.addMessage(this.player.fighter.scroll ? `Equipped ${itemEnt.name}` : `Unequipped ${itemEnt.name}`);
                    } else if (itemEnt.equippable.slot === 'weapon') {
                        this.player.fighter.weapon = (this.player.fighter.weapon === itemEnt) ? null : itemEnt;
                        this.addMessage(this.player.fighter.weapon ? `Equipped ${itemEnt.name}` : `Unequipped ${itemEnt.name}`);
                    }
                } else if (itemEnt.item.useFunc) {
                    this.addMessage(itemEnt.item.useFunc(itemEnt));
                }
                this.updateHUD();
                this.updateInventoryUI();
                this.render();
            };
            list.appendChild(li);
        });
    }

    addMessage(text, color = COLORS.WHITE) {
        const log = document.getElementById('message-log');
        const li = document.createElement('li');
        li.innerText = text;
        li.style.color = color;
        log.appendChild(li);
        log.scrollTop = log.scrollHeight;
    }
}
window.GameEngine = GameEngine;
