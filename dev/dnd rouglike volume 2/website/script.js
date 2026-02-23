document.addEventListener('DOMContentLoaded', () => {
    let selectedClass = null;
    const cards = document.querySelectorAll('.class-card');
    const startBtn = document.getElementById('start-btn');
    const mainMenu = document.getElementById('main-menu');
    const gameContainer = document.getElementById('game-container');

    // Class selection logic
    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Unselect others
            cards.forEach(c => c.classList.remove('selected'));
            // Select this one
            card.classList.add('selected');
            selectedClass = card.dataset.class;
            startBtn.disabled = false;
        });
    });

    // Start game logic
    startBtn.addEventListener('click', () => {
        if (!selectedClass) return;

        // Transitions
        mainMenu.classList.add('hidden');
        gameContainer.classList.remove('hidden');

        // Initialize Engine
        const engine = new window.GameEngine('game-canvas');
        engine.start(selectedClass);

        // Expose engine to console for debugging
        window.engine = engine;
    });

    // Add some subtle hover animations to cards if not already handled by CSS
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            if (!card.classList.contains('selected')) {
                card.style.transform = 'translateY(-2px)';
            }
        });
        card.addEventListener('mouseleave', () => {
            if (!card.classList.contains('selected')) {
                card.style.transform = 'translateY(0)';
            }
        });
    });
});
