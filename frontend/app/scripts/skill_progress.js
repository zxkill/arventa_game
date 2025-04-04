import '../css/skill-progress.css';

const DEFAULT_LEVEL = 1;
const DEFAULT_PERCENT = 0;
const DEFAULT_EXP = '';

function drawProgressWindow(progress) {
    // Инициализация структуры данных
    const categories = {
        armor: {
            skin: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            ore: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            cloth: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP}
        },
        weapon: {
            ore: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            wood: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP}
        },
        tool: {
            wood: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            ore: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            skin: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP}
        },
        craft: {
            wood: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            ore: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            skin: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP},
            cloth: {level: DEFAULT_LEVEL, percent: DEFAULT_PERCENT, exp: DEFAULT_EXP}
        }
    };

    // Заполнение данных
    progress?.forEach(item => {
        const key1 = item.type_item;
        const key2 = item.type_resource;

        if (categories[key1]?.[key2]) {
            categories[key1][key2] = {
                level: item.current_level,
                percent: (item.current_experience * 100) / item.experience_required,
                exp: `${item.current_experience}/${item.experience_required}`
            };
        }
    });

    // Функция для генерации прогресс-бара
    const progressBar = (data, title, resource) => `
        <div class="item-progress">
            <div class="item-name">${title} Ур. ${data.level}</div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.percent}%;"></div>
                    <div class="progress-caption">${data.percent > 0 ? data.exp : ''}</div>
                </div>
            </div>
        </div>
    `;

    // Генерация HTML
    return `
        <div class="skill-window">
            <div class="item-category">
                <h2>Броня</h2>
                ${progressBar(categories.armor.skin, 'Кожа')}
                ${progressBar(categories.armor.ore, 'Латы')}
                ${progressBar(categories.armor.cloth, 'Ткань')}
            </div>
            
            <div class="item-category">
                <h2>Оружие</h2>
                ${progressBar(categories.weapon.ore, 'Меч')}
                ${progressBar(categories.weapon.wood, 'Лук')}
            </div>
            
            <div class="item-category">
                <h2>Инструменты</h2>
                ${progressBar(categories.tool.wood, 'Топор')}
                ${progressBar(categories.tool.ore, 'Кирка')}
                ${progressBar(categories.tool.skin, 'Нож')}
            </div>
            
            <div class="item-category">
                <h2>Крафт</h2>
                ${progressBar(categories.craft.wood, 'Дерево')}
                ${progressBar(categories.craft.ore, 'Металл/Камень')}
                ${progressBar(categories.craft.skin, 'Кожа')}
                ${progressBar(categories.craft.cloth, 'Ткань')}
            </div>
        </div>
    `;
}

const SkillProgress = {drawProgressWindow};
export default SkillProgress;
