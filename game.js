// Constants
const WINDOW_WIDTH = 1400;
const WINDOW_HEIGHT = 900;
const CANVAS_WIDTH = 680;
const CANVAS_HEIGHT = 800;
const LEVEL_HEIGHT = 20000;
const GRAVITY = 0.5;
const JUMP_FORCE = -14;
const MOVE_SPEED = 6;
const PLAYER_SIZE = 45;
const SPRITE_RENDER_SIZE = 200; // Sprites are 200x200 pixels
const BOUNCE_FORCE = -30;
const TRAP_DAMAGE = 25;
const PROJECTILE_SPEED = 10;
const ATTACK_COOLDOWN = 30;

// Colors
const SKY_BLUE = 0x87CEEB;
const CLOUD_WHITE = 0xF8F8FF;
const MOUNTAIN_GRAY = 0xA9A9A9;
const RED = 0xFF6B6B;
const TEAL = 0x4ECDC4;
const GREEN = 0x00FF00;
const FINISH_RED = 0xFF0000;
const BROWN = 0x8B4513;
const CRACKED_BROWN = 0x65320D;
const ORANGE = 0xFFA500;
const BOUNCE_BLUE = 0x00BFFF;
const TRAP_PURPLE = 0x9400D3;
const LAVA_RED = 0xFF4500;
const GOLD = 0xFFD700;

class Projectile {
    constructor(scene, x, y, direction, projectileType, owner) {
        this.scene = scene;
        this.x = x;
        this.y = y;
        this.direction = direction; // 1 for right, -1 for left
        this.type = projectileType; // 'arrow' or 'axe'
        this.width = projectileType === 'arrow' ? 32 : 50;
        this.height = projectileType === 'arrow' ? 32 : 50;
        this.active = true;
        this.lifetime = 120;
        this.owner = owner;

        // Create TWO sprites (one for each view)
        const spriteKey = projectileType === 'arrow' ? 'arrow' : 'axe';
        this.sprite1 = scene.add.sprite(0, 0, spriteKey);
        this.sprite2 = scene.add.sprite(0, 0, spriteKey);

        const scale = projectileType === 'arrow' ? 1.5 : 0.7; // Bigger projectiles
        const originX = projectileType === 'arrow' ? 0 : 0.5;
        const originY = 0.5;

        this.sprite1.setScale(scale);
        this.sprite1.setOrigin(originX, originY);
        this.sprite2.setScale(scale);
        this.sprite2.setOrigin(originX, originY);

        // Flip if going left
        if (direction < 0) {
            this.sprite1.setFlipX(true);
            this.sprite2.setFlipX(true);
        }
    }

    update() {
        this.x += PROJECTILE_SPEED * this.direction;
        this.lifetime -= 1;
        if (this.lifetime <= 0) {
            this.active = false;
        }

        // Deactivate if crossing the screen boundaries (keep within 0-680 range)
        if (this.x < 0 || this.x > CANVAS_WIDTH) {
            this.active = false;
        }
    }

    draw(offsetX, cameraY, viewNum) {
        const sprite = viewNum === 1 ? this.sprite1 : this.sprite2;

        if (!this.active) {
            sprite.setVisible(false);
            return;
        }
        const screenY = this.y - cameraY;
        if (screenY >= -100 && screenY <= CANVAS_HEIGHT + 100) {
            sprite.setPosition(this.x + offsetX, screenY);
            sprite.setVisible(true);
        } else {
            sprite.setVisible(false);
        }
    }

    destroy() {
        this.sprite1.destroy();
        this.sprite2.destroy();
    }

    checkCollision(player) {
        if (this.owner === player || !this.active) return false;
        return this.x < player.x + player.width &&
               this.x + this.width > player.x &&
               this.y < player.y + player.height &&
               this.y + this.height > player.y;
    }
}

class ConfettiParticle {
    constructor(scene, x, y) {
        this.scene = scene;
        this.x = x;
        this.y = y;
        this.vx = Phaser.Math.Between(-8, 8);
        this.vy = Phaser.Math.Between(-15, -5);
        this.gravity = 0.5;
        this.colors = [RED, TEAL, GOLD, GREEN, ORANGE, BOUNCE_BLUE];
        this.color = Phaser.Utils.Array.GetRandom(this.colors);
        this.size = Phaser.Math.Between(3, 8);
        this.life = 120;
        this.maxLife = this.life;

        this.graphics = scene.add.graphics();
    }

    update() {
        this.vx *= 0.98;
        this.vy += this.gravity;
        this.x += this.vx;
        this.y += this.vy;
        this.life -= 1;
        return this.life > 0;
    }

    draw(offsetX, cameraY) {
        const screenY = this.y - cameraY;
        if (screenY >= 0 && screenY <= CANVAS_HEIGHT) {
            const alpha = Math.min(1, this.life / this.maxLife);
            this.graphics.clear();
            this.graphics.fillStyle(this.color, alpha);
            this.graphics.fillCircle(this.x + offsetX, screenY, this.size);
        }
    }

    destroy() {
        this.graphics.destroy();
    }
}

class Player {
    constructor(scene, x, y, color, spriteFolder, playerNum) {
        this.scene = scene;
        this.x = x;
        this.y = y;
        this.width = PLAYER_SIZE;
        this.height = PLAYER_SIZE;
        this.vx = 0;
        this.vy = 0;
        this.color = color;
        this.onGround = false;
        this.finished = false;
        this.cameraY = 0;
        this.highestY = y;
        this.respawnTimer = 0;
        this.respawning = false;
        this.health = 100;
        this.invincibleTimer = 0;
        this.spriteFolder = spriteFolder;
        this.playerNum = playerNum;
        this.animationFrame = 0;
        this.animationTimer = 0;
        this.facingRight = true;
        this.attackCooldown = 0;
        this.isAttacking = false;
        this.attackTimer = 0;

        // Create TWO sprites for this player (one for each view)
        const spriteKey = spriteFolder === 'Orc' ? 'orcIdle' : 'soldierIdle';
        this.sprite1 = scene.add.sprite(0, 0, spriteKey);
        this.sprite1.setScale(2.0); // Much bigger - 200x200 from 100x100
        this.sprite1.setOrigin(0.5, 1.0); // Origin at bottom center (100% down)
        this.sprite1.play(spriteKey);

        this.sprite2 = scene.add.sprite(0, 0, spriteKey);
        this.sprite2.setScale(2.0);
        this.sprite2.setOrigin(0.5, 1.0); // Origin at bottom center (100% down)
        this.sprite2.play(spriteKey);
    }

    update(platforms) {
        // Apply gravity
        this.vy += GRAVITY;

        // Update position
        this.x += this.vx;
        this.y += this.vy;

        // Update animation
        this.animationTimer += 1;
        if (this.animationTimer >= 8) {
            this.animationTimer = 0;
            this.animationFrame = (this.animationFrame + 1) % 8;
        }

        // Update facing direction and sprite flip
        if (this.vx > 0) {
            this.facingRight = true;
            this.sprite1.setFlipX(false);
            this.sprite2.setFlipX(false);
        } else if (this.vx < 0) {
            this.facingRight = false;
            this.sprite1.setFlipX(true);
            this.sprite2.setFlipX(true);
        }

        // Update animation based on state
        const prefix = this.spriteFolder === 'Orc' ? 'orc' : 'soldier';
        let animKey;
        if (this.invincibleTimer > 0 && !this.respawning) {
            animKey = prefix + 'Hurt';
        } else if (Math.abs(this.vx) > 0) {
            animKey = prefix + 'Walk';
        } else {
            animKey = prefix + 'Idle';
        }

        if (this.sprite1.anims.currentAnim?.key !== animKey) {
            this.sprite1.play(animKey);
            this.sprite2.play(animKey);
        }

        // Update timers
        if (this.invincibleTimer > 0) this.invincibleTimer -= 1;
        if (this.respawning) {
            this.respawnTimer -= 1;
            if (this.respawnTimer <= 0) this.respawning = false;
        }
        if (this.attackCooldown > 0) this.attackCooldown -= 1;
        if (this.attackTimer > 0) {
            this.attackTimer -= 1;
        } else {
            this.isAttacking = false;
        }

        // Reset ground state
        this.onGround = false;

        // Check platform collisions
        for (let platform of platforms) {
            if (this.x < platform.x + platform.width &&
                this.x + this.width > platform.x &&
                this.y < platform.y + platform.height &&
                this.y + this.height > platform.y) {

                if (platform.state === 'broken') continue;

                // Landing on top
                if (this.vy > 0 && this.y < platform.y) {
                    this.y = platform.y - this.height;
                    this.vy = 0;
                    this.onGround = true;

                    // Handle special platform types
                    if (platform.type === 'bounce') {
                        this.vy = BOUNCE_FORCE;
                        this.onGround = false;
                    } else if (platform.type === 'trap' && this.invincibleTimer <= 0) {
                        this.takeDamage(TRAP_DAMAGE);
                    } else if (platform.type === 'lava' && this.invincibleTimer <= 0) {
                        this.takeDamage(TRAP_DAMAGE * 2);
                    }

                    // Start cracking normal platforms
                    if (platform.state === 'normal' && platform.type === 'normal') {
                        platform.state = 'cracking';
                        platform.crackTimer = 120;
                    }
                }
                // Other collisions
                else if (this.vy < 0 && this.y > platform.y) {
                    this.y = platform.y + platform.height;
                    this.vy = 0;
                } else if (this.vx > 0) {
                    this.x = platform.x - this.width;
                } else if (this.vx < 0) {
                    this.x = platform.x + platform.width;
                }
            }
        }

        // Ground collision
        if (this.y + this.height > LEVEL_HEIGHT - 40) {
            this.y = LEVEL_HEIGHT - 40 - this.height;
            this.vy = 0;
            this.onGround = true;
        }

        // Wall collision
        if (this.x < 0) this.x = 0;
        if (this.x + this.width > CANVAS_WIDTH) this.x = CANVAS_WIDTH - this.width;

        // Update camera
        let targetCameraY = this.y - CANVAS_HEIGHT + 200;
        if (targetCameraY < 0) targetCameraY = 0;
        if (targetCameraY > LEVEL_HEIGHT - CANVAS_HEIGHT) {
            targetCameraY = LEVEL_HEIGHT - CANVAS_HEIGHT;
        }
        this.cameraY = targetCameraY;

        // Track highest point
        if (this.y < this.highestY) this.highestY = this.y;

        // Check for fatal fall
        const fallDistance = this.y - this.highestY;
        if (fallDistance > 1000 && !this.respawning) {
            this.respawnCloser();
            return false;
        }

        // Check health
        if (this.health <= 0 && !this.respawning) {
            this.respawnCloser();
            return false;
        }

        // Check finish line
        if (this.y <= 800 && !this.finished) {
            this.finished = true;
            return true;
        }

        this.vx = 0;
        return false;
    }

    jump(jumpSound) {
        if (this.onGround) {
            this.vy = JUMP_FORCE;
            this.onGround = false;
            if (jumpSound) {
                jumpSound.play();
            }
        }
    }

    moveLeft() {
        this.vx = -MOVE_SPEED;
    }

    moveRight() {
        this.vx = MOVE_SPEED;
    }

    attack(projectileType) {
        if (this.attackCooldown <= 0) {
            this.attackCooldown = ATTACK_COOLDOWN;
            this.isAttacking = true;
            this.attackTimer = 10;

            // Create projectile in front of player
            const direction = this.facingRight ? 1 : -1;
            const projWidth = projectileType === 'arrow' ? 32 : 50;
            const projHeight = projectileType === 'arrow' ? 32 : 50;

            // Position projectile centered on player vertically
            let projX;
            if (this.facingRight) {
                projX = this.x + this.width;
            } else {
                projX = this.x - projWidth;
            }

            const projY = this.y + (this.height / 2);
            return new Projectile(this.scene, projX, projY, direction, projectileType, this);
        }
        return null;
    }

    takeDamage(damage) {
        if (this.invincibleTimer <= 0) {
            this.health -= damage;
            this.invincibleTimer = 60;
            return true;
        }
        return false;
    }

    respawnCloser() {
        let respawnY = this.highestY + 500;
        if (respawnY >= LEVEL_HEIGHT - 200) {
            respawnY = LEVEL_HEIGHT - 150;
        }

        this.x = CANVAS_WIDTH / 2;
        this.y = respawnY;
        this.vx = 0;
        this.vy = 0;
        this.onGround = false;
        this.respawning = true;
        this.respawnTimer = 60;
        this.health = 100;
        this.invincibleTimer = 120;
        this.finished = false;
    }

    draw(graphics, offsetX, cameraY, viewNum) {
        const screenY = this.y - cameraY;
        const sprite = viewNum === 1 ? this.sprite1 : this.sprite2;

        // Flash when respawning or taking damage
        if ((this.respawning && Math.floor(this.respawnTimer / 10) % 2) ||
            (this.invincibleTimer > 0 && Math.floor(this.invincibleTimer / 5) % 2)) {
            sprite.setVisible(false);
            return;
        }

        // DEBUG: Draw collision box
        // graphics.lineStyle(2, 0xFF00FF, 0.8); // Pink outline
        // graphics.strokeRect(this.x + offsetX, screenY, this.width, this.height);
        // graphics.fillStyle(this.color, 0.2); // Semi-transparent fill
        // graphics.fillRect(this.x + offsetX, screenY, this.width, this.height);

        // Position sprite (centered horizontally, bottom aligned with collision box)
        // With origin at 1.0 (bottom), the sprite's bottom edge is at the Y position
        // We want the sprite bottom to be at the center/middle of the collision box
        sprite.setVisible(true);
        sprite.setPosition(
            this.x + offsetX + this.width / 2, // Center horizontally
            screenY + (this.height * 2.9) // Position sprite lower - at 70% down the collision box
        );
    }

    updateUI() {
        const finishY = 800;
        let height = Math.max(0, Math.min(100,
            Math.floor((LEVEL_HEIGHT - this.y) / (LEVEL_HEIGHT - finishY) * 100)));

        if (this.finished) height = 100;

        const healthColor = this.health > 50 ? 'rgb(0, 255, 0)' :
                           this.health > 25 ? 'rgb(255, 165, 0)' : 'rgb(255, 0, 0)';

        document.getElementById(`height${this.playerNum}`).textContent = `Height: ${height}%`;
        document.getElementById(`health${this.playerNum}`).textContent = `Health: ${this.health}`;
        document.getElementById(`health${this.playerNum}`).style.color = healthColor;
    }
}

class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });
    }

    preload() {
        // Load audio files
        this.load.audio('bgMusic', 'somersaults-edm-ost-track-176960.mp3');
        this.load.audio('jumpSound', 'jump_sound_trimmed.wav');
        this.load.audio('winnerSound', 'winner-game-sound-404167.mp3');

        // Load Orc sprite sheets
        this.load.spritesheet('orcIdle', 'Characters(100x100)/Orc/Orc/Orc-Idle.png', {
            frameWidth: 100,
            frameHeight: 100
        });
        this.load.spritesheet('orcWalk', 'Characters(100x100)/Orc/Orc/Orc-Walk.png', {
            frameWidth: 100,
            frameHeight: 100
        });
        this.load.spritesheet('orcHurt', 'Characters(100x100)/Orc/Orc/Orc-Hurt.png', {
            frameWidth: 100,
            frameHeight: 100
        });

        // Load Soldier sprite sheets
        this.load.spritesheet('soldierIdle', 'Characters(100x100)/Soldier/Soldier/Soldier-Idle.png', {
            frameWidth: 100,
            frameHeight: 100
        });
        this.load.spritesheet('soldierWalk', 'Characters(100x100)/Soldier/Soldier/Soldier-Walk.png', {
            frameWidth: 100,
            frameHeight: 100
        });
        this.load.spritesheet('soldierHurt', 'Characters(100x100)/Soldier/Soldier/Soldier-Hurt.png', {
            frameWidth: 100,
            frameHeight: 100
        });

        // Load arrow sprite
        this.load.image('arrow', 'Arrow01(32x32).png');

        // Load axe sprite
        this.load.image('axe', 'Characters(100x100)/Orc/Orc(Split Effects)/Orc-attack01_Effect.png');
    }

    create() {
        this.gameWon = false;
        this.winner = null;
        this.confettiParticles = [];
        this.projectiles = [];

        // Create animations
        // Orc animations
        this.anims.create({
            key: 'orcIdle',
            frames: this.anims.generateFrameNumbers('orcIdle', { start: 0, end: 5 }),
            frameRate: 10,
            repeat: -1
        });
        this.anims.create({
            key: 'orcWalk',
            frames: this.anims.generateFrameNumbers('orcWalk', { start: 0, end: 7 }),
            frameRate: 10,
            repeat: -1
        });
        this.anims.create({
            key: 'orcHurt',
            frames: this.anims.generateFrameNumbers('orcHurt', { start: 0, end: 3 }),
            frameRate: 10,
            repeat: -1
        });

        // Soldier animations
        this.anims.create({
            key: 'soldierIdle',
            frames: this.anims.generateFrameNumbers('soldierIdle', { start: 0, end: 5 }),
            frameRate: 10,
            repeat: -1
        });
        this.anims.create({
            key: 'soldierWalk',
            frames: this.anims.generateFrameNumbers('soldierWalk', { start: 0, end: 7 }),
            frameRate: 10,
            repeat: -1
        });
        this.anims.create({
            key: 'soldierHurt',
            frames: this.anims.generateFrameNumbers('soldierHurt', { start: 0, end: 3 }),
            frameRate: 10,
            repeat: -1
        });

        // Create graphics for drawing
        this.graphics1 = this.add.graphics();
        this.graphics2 = this.add.graphics();

        // Setup audio
        this.bgMusic = this.sound.add('bgMusic', { loop: true, volume: 0.5 });
        this.jumpSound = this.sound.add('jumpSound', { volume: 0.3 });
        this.winnerSound = this.sound.add('winnerSound', { volume: 0.6 });

        // Start background music
        this.bgMusic.play();

        // Generate level
        this.platforms = this.generateLevel();

        // Create players
        this.player1 = new Player(this, 100, LEVEL_HEIGHT - 150, RED, 'Orc', 1);
        this.player2 = new Player(this, 100, LEVEL_HEIGHT - 150, TEAL, 'Soldier', 2);

        // Setup input
        this.cursors = this.input.keyboard.createCursorKeys();
        this.wasd = this.input.keyboard.addKeys({
            up: Phaser.Input.Keyboard.KeyCodes.W,
            left: Phaser.Input.Keyboard.KeyCodes.A,
            right: Phaser.Input.Keyboard.KeyCodes.D,
            attack: Phaser.Input.Keyboard.KeyCodes.S
        });

        // Reset button
        document.getElementById('reset-btn').onclick = () => this.resetGame();
    }

    generateLevel() {
        const platforms = [];

        // Ground
        platforms.push({
            x: 0,
            y: LEVEL_HEIGHT - 40,
            width: CANVAS_WIDTH,
            height: 40,
            state: 'solid',
            type: 'normal',
            crackTimer: 0
        });

        // Generate platforms
        const seed = Math.random();
        const numPlatforms = 200;

        for (let i = 0; i < numPlatforms; i++) {
            const x = 50 + ((seed + i * 0.3) % 1) * (CANVAS_WIDTH - 200);
            const y = LEVEL_HEIGHT - 200 - (i * 95);
            let width = 80 + ((seed + i * 0.5) % 1) * 100;

            let elementType = 'normal';
            if (i % 6 === 0 && i > 0) {
                elementType = 'bounce';
                width = 60;
            } else if (i % 10 === 0 && i > 5) {
                elementType = 'trap';
                width = 40;
            } else if (i % 15 === 0 && i > 10) {
                elementType = 'lava';
                width = 70;
            }

            platforms.push({
                x, y, width,
                height: 25,
                state: 'normal',
                type: elementType,
                crackTimer: 0
            });
        }

        return platforms;
    }

    updatePlatforms() {
        for (let platform of this.platforms) {
            if (platform.state === 'cracking') {
                platform.crackTimer -= 1;
                if (platform.crackTimer <= 0) {
                    platform.state = 'broken';
                } else if (platform.crackTimer <= 30) {
                    platform.state = 'about_to_break';
                }
            }
        }
    }

    drawBackground(graphics, offsetX, cameraY) {
        // Sky gradient
        for (let y = 0; y < CANVAS_HEIGHT; y += 10) {
            const ratio = y / CANVAS_HEIGHT;
            const r = Math.floor(135 + (248 - 135) * ratio);
            const g = Math.floor(206 + (248 - 206) * ratio);
            const b = Math.floor(235 + (255 - 235) * ratio);
            graphics.fillStyle(Phaser.Display.Color.GetColor(r, g, b));
            graphics.fillRect(offsetX, y, CANVAS_WIDTH, 10);
        }

        // Clouds
        const cloudOffset = Math.floor(cameraY * 0.2) % 150;
        for (let i = 0; i < 10; i++) {
            const cloudX = offsetX + (i * 120 + cloudOffset) % CANVAS_WIDTH;
            const cloudY = 50 + (i * 60) % 300;
            graphics.fillStyle(CLOUD_WHITE);
            for (let j = 0; j < 3; j++) {
                graphics.fillCircle(cloudX + j * 15, cloudY, 20 + j * 5);
            }
        }

        // Mountains
        graphics.fillStyle(MOUNTAIN_GRAY);
        graphics.beginPath();
        graphics.moveTo(offsetX, CANVAS_HEIGHT);
        for (let i = 0; i < 12; i++) {
            const x = offsetX + (i * 60);
            const y = 300 + (i % 4) * 80 + Math.floor(50 * Math.sin(i * 0.5));
            graphics.lineTo(x, y);
        }
        graphics.lineTo(offsetX + CANVAS_WIDTH, CANVAS_HEIGHT);
        graphics.closePath();
        graphics.fillPath();
    }

    drawLevel(graphics, offsetX, cameraY) {
        this.drawBackground(graphics, offsetX, cameraY);

        // Start line
        const startScreenY = LEVEL_HEIGHT - 40 - cameraY;
        if (startScreenY >= -100 && startScreenY <= CANVAS_HEIGHT + 100) {
            graphics.fillStyle(GREEN);
            graphics.fillRect(offsetX, startScreenY, CANVAS_WIDTH, 40);
        }

        // Finish line
        const finishScreenY = 760 - cameraY;
        if (finishScreenY >= -100 && finishScreenY <= CANVAS_HEIGHT + 100) {
            graphics.fillStyle(FINISH_RED);
            graphics.fillRect(offsetX, finishScreenY, CANVAS_WIDTH, 40);
        }

        // Platforms
        for (let platform of this.platforms) {
            const screenY = platform.y - cameraY;
            if (screenY >= -100 && screenY <= CANVAS_HEIGHT + 100) {
                let color;
                if (platform.type === 'bounce') color = BOUNCE_BLUE;
                else if (platform.type === 'trap') color = TRAP_PURPLE;
                else if (platform.type === 'lava') color = LAVA_RED;
                else if (platform.state === 'cracking') color = CRACKED_BROWN;
                else if (platform.state === 'about_to_break') {
                    color = Math.floor(platform.crackTimer / 5) % 2 ? ORANGE : CRACKED_BROWN;
                } else if (platform.state === 'broken') continue;
                else color = BROWN;

                graphics.fillStyle(color);
                graphics.fillRect(platform.x + offsetX, screenY, platform.width, platform.height);

                // Special effects
                if (platform.type === 'bounce') {
                    graphics.fillStyle(0xFFFFFF);
                    graphics.fillCircle(platform.x + offsetX + platform.width/2,
                                      screenY + platform.height/2, 8);
                } else if (platform.type === 'trap') {
                    graphics.fillStyle(0xFFFFFF);
                    for (let spike = 0; spike < platform.width; spike += 10) {
                        const spikeX = platform.x + offsetX + spike;
                        graphics.fillTriangle(
                            spikeX, screenY,
                            spikeX + 5, screenY - 8,
                            spikeX + 10, screenY
                        );
                    }
                } else if (platform.type === 'lava') {
                    graphics.fillStyle(ORANGE);
                    for (let bubble = 0; bubble < platform.width; bubble += 15) {
                        const bubbleX = platform.x + offsetX + bubble + 7;
                        graphics.fillCircle(bubbleX, screenY + 5, 3);
                    }
                }

                // Cracks
                if (platform.state === 'cracking' || platform.state === 'about_to_break') {
                    graphics.lineStyle(2, 0x000000);
                    const midX = platform.x + offsetX + platform.width / 2;
                    const midY = screenY + platform.height / 2;
                    graphics.lineBetween(midX, screenY, midX, screenY + platform.height);
                    graphics.lineBetween(platform.x + offsetX, midY,
                                       platform.x + offsetX + platform.width, midY);
                }
            }
        }
    }

    createConfetti(x, y) {
        for (let i = 0; i < 50; i++) {
            const px = x + Phaser.Math.Between(-30, 30);
            const py = y + Phaser.Math.Between(-30, 30);
            this.confettiParticles.push(new ConfettiParticle(this, px, py));
        }
    }

    updateConfetti() {
        this.confettiParticles = this.confettiParticles.filter(p => p.update());
    }

    update() {
        if (!this.gameWon) {
            // Handle input - Player 1 (Orc - WASD + S for attack)
            if (this.wasd.left.isDown) this.player1.moveLeft();
            if (this.wasd.right.isDown) this.player1.moveRight();
            if (this.wasd.up.isDown) this.player1.jump(this.jumpSound);
            if (this.wasd.attack.isDown) {
                const projectile = this.player1.attack('axe');
                if (projectile) this.projectiles.push(projectile);
            }

            // Handle input - Player 2 (Soldier - Arrows + Down for attack)
            if (this.cursors.left.isDown) this.player2.moveLeft();
            if (this.cursors.right.isDown) this.player2.moveRight();
            if (this.cursors.up.isDown) this.player2.jump(this.jumpSound);
            if (this.cursors.down.isDown) {
                const projectile = this.player2.attack('arrow');
                if (projectile) this.projectiles.push(projectile);
            }

            // Update platforms
            this.updatePlatforms();

            // Update players
            if (this.player1.update(this.platforms) && !this.gameWon) {
                this.gameWon = true;
                this.winner = 1;
                this.createConfetti(this.player1.x + this.player1.width/2,
                                  this.player1.y + this.player1.height/2);
                this.winnerSound.play();
                document.getElementById('status1').textContent = 'EPIC WINNER!';
                document.getElementById('status1').style.color = 'gold';
                document.getElementById('status2').textContent = 'Try again!';
            }

            if (this.player2.update(this.platforms) && !this.gameWon) {
                this.gameWon = true;
                this.winner = 2;
                this.createConfetti(this.player2.x + this.player2.width/2,
                                  this.player2.y + this.player2.height/2);
                this.winnerSound.play();
                document.getElementById('status2').textContent = 'EPIC WINNER!';
                document.getElementById('status2').style.color = 'gold';
                document.getElementById('status1').textContent = 'Try again!';
            }

            // Update projectiles
            for (let i = this.projectiles.length - 1; i >= 0; i--) {
                const projectile = this.projectiles[i];
                projectile.update();

                if (!projectile.active) {
                    projectile.destroy();
                    this.projectiles.splice(i, 1);
                    continue;
                }

                // Check collision with players (but not the owner)
                if (projectile.checkCollision(this.player1)) {
                    this.player1.takeDamage(10);
                    projectile.active = false;
                    projectile.destroy();
                    this.projectiles.splice(i, 1);
                } else if (projectile.checkCollision(this.player2)) {
                    this.player2.takeDamage(10);
                    projectile.active = false;
                    projectile.destroy();
                    this.projectiles.splice(i, 1);
                }
            }

            // Update UI
            this.player1.updateUI();
            this.player2.updateUI();
        }

        // Update confetti
        this.updateConfetti();

        // Clear all graphics
        this.graphics1.clear();
        this.graphics2.clear();

        // Draw Player 1's view (left side)
        this.drawLevel(this.graphics1, 10, this.player1.cameraY);
        this.player1.draw(this.graphics1, 10, this.player1.cameraY, 1);
        this.player2.draw(this.graphics1, 10, this.player1.cameraY, 1);

        // Draw projectiles for player 1's view (only show player 1's projectiles)
        for (let projectile of this.projectiles) {
            if (projectile.owner === this.player1) {
                projectile.draw(10, this.player1.cameraY, 1);
            } else {
                projectile.sprite1.setVisible(false); // Hide other player's projectiles
            }
        }

        for (let particle of this.confettiParticles) {
            particle.draw(10, this.player1.cameraY);
        }

        // Draw Player 2's view (right side)
        this.drawLevel(this.graphics2, 710, this.player2.cameraY);
        this.player1.draw(this.graphics2, 710, this.player2.cameraY, 2);
        this.player2.draw(this.graphics2, 710, this.player2.cameraY, 2);

        // Draw projectiles for player 2's view (only show player 2's projectiles)
        for (let projectile of this.projectiles) {
            if (projectile.owner === this.player2) {
                projectile.draw(710, this.player2.cameraY, 2);
            } else {
                projectile.sprite2.setVisible(false); // Hide other player's projectiles
            }
        }

        for (let particle of this.confettiParticles) {
            particle.draw(710, this.player2.cameraY);
        }

        // Draw divider
        this.graphics1.lineStyle(5, GOLD);
        this.graphics1.lineBetween(700, 0, 700, WINDOW_HEIGHT);
    }

    resetGame() {
        // Clear confetti
        this.confettiParticles.forEach(p => p.destroy());
        this.confettiParticles = [];

        // Clear projectiles
        this.projectiles.forEach(p => p.destroy());
        this.projectiles = [];

        // Reset game state
        this.gameWon = false;
        this.winner = null;

        // Reset players
        this.player1.x = 100;
        this.player1.y = LEVEL_HEIGHT - 150;
        this.player1.vx = 0;
        this.player1.vy = 0;
        this.player1.health = 100;
        this.player1.finished = false;
        this.player1.highestY = LEVEL_HEIGHT - 150;
        this.player1.respawning = false;
        this.player1.invincibleTimer = 0;
        this.player1.attackCooldown = 0;
        this.player1.isAttacking = false;
        this.player1.attackTimer = 0;

        this.player2.x = 100;
        this.player2.y = LEVEL_HEIGHT - 150;
        this.player2.vx = 0;
        this.player2.vy = 0;
        this.player2.health = 100;
        this.player2.finished = false;
        this.player2.highestY = LEVEL_HEIGHT - 150;
        this.player2.respawning = false;
        this.player2.invincibleTimer = 0;
        this.player2.attackCooldown = 0;
        this.player2.isAttacking = false;
        this.player2.attackTimer = 0;

        // Regenerate level
        this.platforms = this.generateLevel();

        // Reset UI
        document.getElementById('status1').textContent = '';
        document.getElementById('status1').style.color = 'white';
        document.getElementById('status2').textContent = '';
        document.getElementById('status2').style.color = 'white';
    }
}

// Phaser configuration
const config = {
    type: Phaser.AUTO,
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    parent: 'game-container',
    backgroundColor: '#000000',
    scene: GameScene
};

const game = new Phaser.Game(config);
