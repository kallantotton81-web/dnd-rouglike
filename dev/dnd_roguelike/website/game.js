const TILE_SIZE = 20;
const MAP_WIDTH = 40;
const MAP_HEIGHT = 25;
const FOV_RADIUS = 8;
const BASE_AC = 10;

const COLORS = {
    BLACK: '#0c0c0e',
    WHITE: '#e0e0e0',
    GREY: '#646464',
    DARK_GREY: '#323232',
    RED: '#ff4b2b',
    GREEN: '#50c878',
    BLUE: '#00ffff',
    GOLD: '#ffd700',
    YELLOW: '#ffff00'
};

class Rect {
    constructor(x, y, w, h) {
        this.x1 = x;
        this.y1 = y;
        this.x2 = x + w;
        this.y2 = y + h;
    }
    center() {
        return {
            x: Math.floor((this.x1 + this.x2) / 2),
            y: Math.floor((this.y1 + this.y2) / 2)
        };
    }
    intersect(other) {
        return (this.x1 <= other.x2 && this.x2 >= other.x1 &&
            this.y1 <= other.y2 && this.y2 >= other.y1);
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

class Entity {
    constructor(x, y, name, char, color) {
        this.x = x;
        this.y = y;
        this.name = name;
        this.char = char;
        this.color = color;
        this.strength = 10;
        this.dexterity = 10;
        this.constitution = 10;
        this.hp = 10;
        this.maxHp = 10;
        this.ac = BASE_AC;
        this.equipment = { armor: null, weapon: null };
    }

    getModifier(stat) {
        return Math.floor((stat - 10) / 2);
    }

    get armorClass() {
        let dexMod = this.getModifier(this.dexterity);
        let armor = this.equipment.armor;
        if (armor) {
            let effectiveDexMod = dexMod;
            if (armor.dexCap !== null) effectiveDexMod = Math.min(dexMod, armor.dexCap);
            return BASE_AC + armor.bonus + effectiveDexMod;
        }
        return this.ac + dexMod;
    }
}

class Item {
    constructor(x, y, name, char, color) {
        this.x = x;
        this.y = y;
        this.name = name;
        this.char = char;
        this.color = color;
    }
}

class Armor extends Item {
    constructor(x, y, name, bonus, dexCap = null) {
        super(x, y, name, '[', COLORS.GOLD);
        this.bonus = bonus;
        this.dexCap = dexCap;
    }
}

class Weapon extends Item {
    constructor(x, y, name, color, dice, sides) {
        super(x, y, name, '/', color);
        this.dice = dice;
        this.sides = sides;
    }
}

class HealingPotion extends Item {
    constructor(x, y, amount) {
        super(x, y, "Healing Potion", '!', COLORS.GREEN);
        this.amount = amount;
    }
}


class GameEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.map = [];
        this.entities = [];
        this.items = [];
        this.player = null;
        this.messageLog = [];
        this.init();
    }

    init() {
        this.generateMap();
        this.spawnMonsters(30);
        this.spawnItems(5);
        this.addMessage("Welcome to the Full Web Edition!", COLORS.GOLD);
        this.computeFOV();
        this.render();
        window.addEventListener('keydown', (e) => this.handleInput(e));
    }

    generateMap() {
        // Initialize with walls
        for (let x = 0; x < MAP_WIDTH; x++) {
            this.map[x] = [];
            for (let y = 0; y < MAP_HEIGHT; y++) {
                this.map[x][y] = new Tile(true);
            }
        }

        let rooms = [];
        const MAX_ROOMS = 15;
        const MIN_SIZE = 4;
        const MAX_SIZE = 8;

        for (let r = 0; r < MAX_ROOMS; r++) {
            let w = Math.floor(Math.random() * (MAX_SIZE - MIN_SIZE)) + MIN_SIZE;
            let h = Math.floor(Math.random() * (MAX_SIZE - MIN_SIZE)) + MIN_SIZE;
            let x = Math.floor(Math.random() * (MAP_WIDTH - w - 1));
            let y = Math.floor(Math.random() * (MAP_HEIGHT - h - 1));

            let newRoom = new Rect(x, y, w, h);
            if (!rooms.some(other => newRoom.intersect(other))) {
                this.createRoom(newRoom);
                let center = newRoom.center();

                if (rooms.length === 0) {
                    this.player = new Entity(center.x, center.y, 'Player', '@', COLORS.WHITE);
                    this.player.strength = 16;
                    this.player.dexterity = 14;
                    this.player.constitution = 14;
                    this.player.maxHp = 30 + this.player.getModifier(this.player.constitution);
                    this.player.hp = this.player.maxHp;
                    this.entities.push(this.player);
                } else {
                    let prev = rooms[rooms.length - 1].center();
                    if (Math.random() > 0.5) {
                        this.createHTunnel(prev.x, center.x, prev.y);
                        this.createVTunnel(prev.y, center.y, center.x);
                    } else {
                        this.createVTunnel(prev.y, center.y, prev.x);
                        this.createHTunnel(prev.x, center.x, center.y);
                    }
                }
                rooms.push(newRoom);
            }
        }
    }

    createRoom(room) {
        for (let x = room.x1 + 1; x < room.x2; x++) {
            for (let y = room.y1 + 1; y < room.y2; y++) {
                this.map[x][y].blocked = false;
                this.map[x][y].blockSight = false;
            }
        }
    }

    createHTunnel(x1, x2, y) {
        for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
            this.map[x][y].blocked = false;
            this.map[x][y].blockSight = false;
        }
    }

    createVTunnel(y1, y2, x) {
        for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
            this.map[x][y].blocked = false;
            this.map[x][y].blockSight = false;
        }
    }

    spawnMonsters(num) {
        for (let i = 0; i < num; i++) {
            let x = Math.floor(Math.random() * MAP_WIDTH);
            let y = Math.floor(Math.random() * MAP_HEIGHT);
            if (!this.map[x][y].blocked && !this.entities.some(e => e.x === x && e.y === y)) {
                let r = Math.random();
                let monster;
                if (r < 0.6) monster = new Entity(x, y, 'Orc', 'o', COLORS.RED);
                else if (r < 0.9) monster = new Entity(x, y, 'Goblin', 'g', COLORS.GREEN);
                else {
                    monster = new Entity(x, y, 'Troll', 'T', '#4169e1');
                    monster.hp = 20; monster.maxHp = 20; monster.ac = 15;
                }
                this.entities.push(monster);
            }
        }
    }

    spawnItems(num) {
        // Spawn 1 Sword of Infinite Damage
        let sx, sy;
        do {
            sx = Math.floor(Math.random() * MAP_WIDTH);
            sy = Math.floor(Math.random() * MAP_HEIGHT);
        } while (this.map[sx][sy].blocked);
        this.items.push(new Weapon(sx, sy, "Sword of Infinite Damage", COLORS.BLUE, 100000, 10));

        // Spawn some armor
        for (let i = 0; i < num; i++) {
            let x, y;
            do {
                x = Math.floor(Math.random() * MAP_WIDTH);
                y = Math.floor(Math.random() * MAP_HEIGHT);
            } while (this.map[x][y].blocked || this.items.some(item => item.x === x && item.y === y));

            let r = Math.random();
            if (r < 0.5) this.items.push(new Armor(x, y, "Leather Armor", 1, null));
            else if (r < 0.8) this.items.push(new Armor(x, y, "Chain Mail", 6, 0));
            else this.items.push(new Armor(x, y, "Plate Armor", 8, 0));
        }

        // Spawn some potions
        for (let i = 0; i < 5; i++) {
            let x, y;
            do {
                x = Math.floor(Math.random() * MAP_WIDTH);
                y = Math.floor(Math.random() * MAP_HEIGHT);
            } while (this.map[x][y].blocked || this.items.some(item => item.x === x && item.y === y));
            this.items.push(new HealingPotion(x, y, 10));
        }
    }


    addMessage(text, color = COLORS.WHITE) {
        this.messageLog.push({ text, color });
        if (this.messageLog.length > 5) this.messageLog.shift();
    }

    handleInput(e) {
        let dx = 0, dy = 0;
        switch (e.key.toLowerCase()) {
            case 'w': case 'arrowup': dy = -1; break;
            case 's': case 'arrowdown': dy = 1; break;
            case 'a': case 'arrowleft': dx = -1; break;
            case 'd': case 'arrowright': dx = 1; break;
            case 'g': this.pickUpItem(); break;
        }
        if (dx !== 0 || dy !== 0) this.moveOrAttack(dx, dy);
    }

    moveOrAttack(dx, dy) {
        let destX = this.player.x + dx;
        let destY = this.player.y + dy;
        let target = this.entities.find(e => e.x === destX && e.y === destY && e !== this.player);
        if (target) this.attack(this.player, target);
        else if (!this.map[destX][destY].blocked) {
            this.player.x = destX;
            this.player.y = destY;
        }
        this.handleMonsterTurns();
        this.computeFOV();
        this.render();
    }

    attack(attacker, target) {
        let roll = Math.floor(Math.random() * 20) + 1;
        let mod = attacker.getModifier(attacker.strength);
        let attackRoll = roll + mod;

        if (roll === 20) {
            let damage = 0;
            if (attacker.equipment.weapon) {
                for (let i = 0; i < attacker.equipment.weapon.dice * 2; i++) damage += Math.floor(Math.random() * attacker.equipment.weapon.sides) + 1;
            } else {
                damage = (Math.floor(Math.random() * 8) + 1) + (Math.floor(Math.random() * 8) + 1);
            }
            damage += mod;
            target.hp -= damage;
            this.addMessage(`CRITICAL! ${attacker.name} hits ${target.name} for ${damage}!`, COLORS.GREEN);
        } else if (roll === 1) {
            this.addMessage(`${attacker.name} misses miserably!`, COLORS.RED);
        } else if (attackRoll >= target.armorClass) {
            let damage = 0;
            if (attacker.equipment.weapon) {
                for (let i = 0; i < attacker.equipment.weapon.dice; i++) damage += Math.floor(Math.random() * attacker.equipment.weapon.sides) + 1;
            } else {
                damage = Math.floor(Math.random() * 8) + 1;
            }
            damage += mod;
            target.hp -= damage;
            this.addMessage(`${attacker.name} hits ${target.name} for ${damage} (Roll: ${attackRoll})`, COLORS.WHITE);
        } else {
            this.addMessage(`${attacker.name} misses! (Roll: ${attackRoll} vs AC ${target.armorClass})`, COLORS.GREY);
        }

        if (target.hp <= 0) {
            this.addMessage(`${target.name} dies!`, COLORS.RED);
            this.entities = this.entities.filter(e => e !== target);
        }
    }

    pickUpItem() {
        let idx = this.items.findIndex(i => i.x === this.player.x && i.y === this.player.y);
        if (idx > -1) {
            let item = this.items[idx];
            if (item instanceof Armor) {
                this.player.equipment.armor = item;
                this.addMessage(`Equipped ${item.name}! AC is now ${this.player.armorClass}`, COLORS.GOLD);
                this.items.splice(idx, 1);
            } else if (item instanceof Weapon) {
                this.player.equipment.weapon = item;
                this.addMessage(`Equipped ${item.name}!`, COLORS.BLUE);
                this.items.splice(idx, 1);
            } else if (item instanceof HealingPotion) {
                if (this.player.hp < this.player.maxHp) {
                    let heal = Math.min(this.player.maxHp - this.player.hp, item.amount);
                    this.player.hp += heal;
                    this.addMessage(`Drank ${item.name} and healed for ${heal} HP!`, COLORS.GREEN);
                    this.items.splice(idx, 1);
                } else {
                    this.addMessage(`You are already at full health.`, COLORS.WHITE);
                    return; // Don't consume or skip turn if already full
                }
            }
            this.handleMonsterTurns();
            this.render();
        }
    }


    handleMonsterTurns() {
        this.entities.filter(e => e !== this.player).forEach(m => {
            let dx = 0, dy = 0;
            if (Math.abs(m.x - this.player.x) <= 5 && Math.abs(m.y - this.player.y) <= 5) {
                if (m.x < this.player.x) dx = 1; else if (m.x > this.player.x) dx = -1;
                if (m.y < this.player.y) dy = 1; else if (m.y > this.player.y) dy = -1;
            }
            if (dx !== 0 || dy !== 0) {
                let tx = m.x + dx, ty = m.y + dy;
                if (tx === this.player.x && ty === this.player.y) this.attack(m, this.player);
                else if (!this.map[tx][ty].blocked && !this.entities.some(e => e.x === tx && e.y === ty)) {
                    m.x = tx; m.y = ty;
                }
            }
        });
    }

    computeFOV() {
        for (let x = 0; x < MAP_WIDTH; x++) {
            for (let y = 0; y < MAP_HEIGHT; y++) this.map[x][y].visible = false;
        }
        for (let i = 0; i < 360; i += 1) {
            let rad = i * Math.PI / 180;
            for (let r = 0; r < FOV_RADIUS; r++) {
                let x = Math.round(this.player.x + Math.cos(rad) * r);
                let y = Math.round(this.player.y + Math.sin(rad) * r);
                if (x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT) {
                    this.map[x][y].visible = true;
                    this.map[x][y].explored = true;
                    if (this.map[x][y].blockSight) break;
                }
            }
        }
    }

    render() {
        this.ctx.fillStyle = COLORS.BLACK;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.font = `${TILE_SIZE - 2}px monospace`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        for (let x = 0; x < MAP_WIDTH; x++) {
            for (let y = 0; y < MAP_HEIGHT; y++) {
                let t = this.map[x][y];
                if (!t.explored) continue;
                this.ctx.fillStyle = t.visible ? '#222' : '#0a0a0a';
                this.ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                if (t.blocked) {
                    this.ctx.fillStyle = t.visible ? COLORS.GREY : '#1a1a1a';
                    this.ctx.fillText('#', x * TILE_SIZE + 10, y * TILE_SIZE + 10);
                }
            }
        }

        this.items.forEach(i => {
            if (this.map[i.x][i.y].visible) {
                this.ctx.fillStyle = i.color;
                this.ctx.fillText(i.char, i.x * TILE_SIZE + 10, i.y * TILE_SIZE + 10);
            }
        });

        this.entities.forEach(e => {
            if (this.map[e.x][e.y].visible) {
                this.ctx.fillStyle = e.color;
                this.ctx.fillText(e.char, e.x * TILE_SIZE + 10, e.y * TILE_SIZE + 10);
            }
        });

        this.renderUI();
    }

    renderUI() {
        this.ctx.fillStyle = 'rgba(0,0,0,0.8)';
        this.ctx.fillRect(0, this.canvas.height - 100, this.canvas.width, 100);
        this.ctx.font = '14px sans-serif';
        this.ctx.textAlign = 'left';
        let y = this.canvas.height - 80;
        this.messageLog.forEach(m => {
            this.ctx.fillStyle = m.color;
            this.ctx.fillText(m.text, 10, y);
            y += 18;
        });

        this.ctx.fillStyle = COLORS.GOLD;
        let arm = this.player.equipment.armor ? this.player.equipment.armor.name : 'None';
        let wpn = this.player.equipment.weapon ? this.player.equipment.weapon.name : 'Unarmed';
        this.ctx.fillText(`HP: ${this.player.hp}/${this.player.maxHp} | AC: ${this.player.armorClass} (${arm}) | WPN: ${wpn}`, 10, 20);
    }
}

document.addEventListener('DOMContentLoaded', () => new GameEngine('game-canvas'));
