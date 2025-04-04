import '../css/main.css'
import '../css/player-window.css'
import '../css/modal.css'
import Variable from "./variable";
import Utils from "./utils";
import {onWebSocketReady, websocketRequest} from "./websocket";
import 'ol/ol.css';  // Импорт стилей
import {Map} from 'ol';
import {View} from 'ol';
import {defaults as defaultControls} from 'ol/control';
import {Feature} from 'ol';
import {Point, Circle} from 'ol/geom';
import {Vector as VectorSource} from 'ol/source';
import {Vector as VectorLayer} from 'ol/layer';
import {Style, Icon, Stroke} from 'ol/style';
import {OSM} from 'ol/source';
import {Tile as TileLayer} from 'ol/layer';
import {fromLonLat} from 'ol/proj';
import {ScaleLine} from 'ol/control';
import {Select} from 'ol/interaction';
import {click} from 'ol/events/condition';
import {toLonLat} from 'ol/proj';
import {getPointResolution} from 'ol/proj';
import XYZ from 'ol/source/XYZ';
import {defaults as defaultInteractions} from 'ol/interaction';
import Modal from "./modal";
import {animatedMine} from "./mine";
import {getMonsterInfo} from "./battle_monster";
import DrawCrafting from "./draw_crafting";
import Profile from "./profile";
import Settings from "./settings";
import Feedback from "./feedback";
import Chat from "./chat";
import PlayerWindow from "./player_window";
import SkillProgress from "./skill_progress";
import Quest from "./quest";
import Portal, {getPortalInfo} from "./portals";
import Mail from "./mail";
import Market from "./market";

document.addEventListener("DOMContentLoaded", async function () {
    onWebSocketReady(async () => {
        let points;
        let selfInfo;
        selfInfo = Variable.getSelfInfo();

        document.addEventListener('contextmenu', (event) => event.preventDefault());

        function setVh() {
            document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
        }

        window.addEventListener('resize', setVh);
        setVh();


        if (!Variable.getUserQuests()) {
            Variable.setUserQuests(await websocketRequest('/quest', {'action': 'get_user_quest'}));
        }

        Quest.updateCountQuest(Variable.getUserQuests());

        if (!Variable.getUserMails()) {
            Variable.setUserMails(await websocketRequest('/mail', {'action': 'get_messages'}));
        }

        Mail.updateCountMail(Variable.getUserMails());

        if (!selfInfo) {
            selfInfo = await websocketRequest('/player', {'action': 'get_self'});
            Variable.setSelfInfo(selfInfo);
            localStorage.setItem('user_info', JSON.stringify(selfInfo));
        }

        if (selfInfo) {
            Utils.updateStatusBar(selfInfo);
        }

        await Settings.applySettings(Variable.getSelfInfo().settings)

        const player_feature = new Feature({
            geometry: new Point(fromLonLat([0, 0])),
        });
        player_feature.setId(selfInfo.id);
        player_feature.setProperties({
            typeObject: 'player',
        });

        // Создание стилей для игрока
        const player_styles = [
            new Style({
                image: new Icon({
                    src: '/img/user.png',
                    scale: 1,
                }),
            }),
            new Style({
                geometry: new Circle(fromLonLat([0, 0]), toOLMeters(Variable.getSelfInfo().interaction_radius, 1.7)),
                stroke: new Stroke({color: 'rgba(234,11,11,0.5)', width: 1}),
            }),
            // new Style({
            //     geometry: new Circle(fromLonLat([0, 0]), 0),
            //     stroke: new Stroke({color: '#F000', width: 2}),
            // }),
        ];

        player_feature.setStyle(player_styles);

        const player_source = new VectorSource({features: [player_feature]});
        const player_layer = new VectorLayer({
            source: player_source,
            name: 'player',
            className: 'ol-layer__player',
            zIndex: 4,
        });

        const points_source = new VectorSource();
        const points_layer = new VectorLayer({
            source: points_source,
            name: 'points',
            className: 'ol-layer__points',
            zIndex: 3,
        });

        const lines_source = new VectorSource();
        const temp_lines_source = new VectorSource();
        const lines_layer = new VectorLayer({
            source: lines_source,
            name: 'lines',
            className: 'ol-layer__lines',
            zIndex: 2,
        });
        const temp_lines_layer = new VectorLayer({
            source: temp_lines_source,
            name: 'lines',
            className: 'ol-layer__lines',
            zIndex: 2,
        });

        const regions_source = new VectorSource();
        const regions_layer = new VectorLayer({
            source: regions_source,
            name: 'regions',
            className: 'ol-layer__regions',
            zIndex: 1,
        });

        const base_layer = new TileLayer({
            className: 'ol-layer__base',
            source: new OSM(),
        });

        const view = new View({
            center: [0, 0],
            zoom: 19,
            minZoom: 1, //17
            maxZoom: 20,
            constrainResolution: true,
        });

        const ViewOffsets = {
            NORMAL: 165,
            CENTER: -10,
        };

        // Источник и слой для маркеров игроков
        const playersSource = new VectorSource();
        const playersLayer = new VectorLayer({
            source: playersSource,
        });

        // Источник и слой для точек
        const pointsSource = new VectorSource();
        const pointsLayer = new VectorLayer({
            source: pointsSource,
        });

        view.setProperties({offset: [0, ViewOffsets.NORMAL]});

        const map = new Map({
            target: 'map',
            layers: [
                base_layer,
                regions_layer,
                lines_layer,
                temp_lines_layer,
                points_layer,
                player_layer,
                playersLayer,
                pointsLayer,
            ],
            view,
            controls: defaultControls().extend([new ScaleLine()]),
            interactions: defaultInteractions({doubleClickZoom: false}),
        });
        let playerCoordinate;
        let show_chat = false;
        setBaselayer();
        // Определение текущих координат пользователя
        if ('geolocation' in navigator) {
            navigator.geolocation.watchPosition(async ({coords}) => {
                const longitude = coords.longitude;
                const latitude = coords.latitude;
                movePlayer([longitude, latitude]);
                playerCoordinate = fromLonLat([longitude, latitude]);
                document.querySelector('#toggle-follow').setAttribute('data-active', (localStorage.getItem('follow') !== 'false'));
                if (!map.getProperties().is_first_watched) {
                    map.setProperties({is_first_watched: true});
                }
                // Отправляем координаты на сервер
                await websocketRequest('/player', {
                    'action': 'update_coordinates',
                    'longitude': longitude,
                    'latitude': latitude
                }).then(async () => {
                });

                // Получаем список ближайших игроков
                await drawNearbyPlayers();

                if (!map.getProperties().is_first_watched) {
                    map.setProperties({is_first_watched: true})
                } else {
                    await debounceDrawPoints;
                }
            }, error => {
                console.error('Geolocation API got an error:', error)
                if (error.code === 1) {
                    /*$('body').empty().css({ display: 'grid' }).append($('<div>', {
                        class: 'fatal-error',
                        text: 'popups.gps.denied'
                    }))*/
                } else if (error.code === 2) {
                    if (Utils.isMobile()) {
                        /*$('body').empty().css({ display: 'grid' }).append($('<div>', {
                            class: 'fatal-error',
                            text: 'gps fail'
                        }))*/
                    } else {
                        //player_source.clear()
                        //$('#self-info__coord').parent().remove()
                        //$('#toggle-follow').remove()
                    }
                } else {
                    //popups.gps.generic
                }
            }, {
                enableHighAccuracy: true,
                maximumAge: 0
            })
        } else {
            /*$('body').empty().css({ display: 'grid' }).append($('<div>', {
                class: 'fatal-error',
                text: 'popups.gps.unavailable'
            }))*/
        }

        //метод для получения регионов на которые разбита земля
        await websocketRequest('/map/getRegions').then(regions => {
            Utils.addRegionsToMap(map, regions, playerCoordinate)
        });

        function toOLMeters(meters, rate = 1 / getPointResolution('EPSG:3857', 1, view.getCenter())) {
            return meters * rate;
        }

        function movePlayer(coords) {
            const pos = fromLonLat(coords)
            player_feature.getGeometry().setCoordinates(pos)
            player_styles.slice(1, 3).forEach(e => e.getGeometry().setCenter(pos))

            ;(function () {
                const follow = localStorage.getItem('follow') !== 'false'
                const {is_first_watched, ignore_follow} = map.getProperties()
                if (is_first_watched && (follow && !ignore_follow)) view.setCenter(pos)
                else if (!is_first_watched && (follow || !ignore_follow)) view.setCenter(pos)
            })();
        }

        function setBaselayer() {
            /*if (type === 'osm') {
                source = new ol.source.OSM({attributions: []})
            } else if (type === 'goo') {
                source = new ol.source.XYZ({url: 'https://mt{0-3}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'})
            } else if (type === 'cdb') {
                const theme = getSettings('theme')
                if (theme === 'auto' && is_dark || theme === 'dark')
                    source = new ol.source.XYZ({url: 'https://{a-c}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'})
                else
                    source = new ol.source.XYZ({url: 'https://{a-c}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'})
            } else source = new ol.source.XYZ({})*/
            // Установка источника для базового слоя
            const source = new XYZ({
                url: 'https://{a-c}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'
            });
            base_layer.setSource(source);

        }

        async function drawNearbyPlayers() {
            //const nearby_players = await apiRequest('/player/nearbyPlayers', 'GET');
            const nearby_players = await websocketRequest('/player', {'action': 'get_nearby_players'});
            // Очищаем старые маркеры и добавляем новых
            playersSource.clear();
            nearby_players.forEach(player => {
                // Условно: сервер возвращает [id, lat, lon]
                addPlayerMarker(player.player_id, player.longitude, player.latitude, 'other_user.png');
            });
        }

        // Обработчик клика на карте
        map.on('click', function (event) {
            // Получение координат клика в формате [долгота, широта] (EPSG:4326)
            const coordinates = new toLonLat(event.coordinate);

            // Вывод координат в консоль
            console.log('Координаты клика: ', coordinates);
        });

        // Обработчик кликов по точкам
        const selectInteraction = new Select({
            condition: click,
            style: null, // Отключаем изменение стиля
        });
        map.addInteraction(selectInteraction);

        selectInteraction.on('select', async function (event) {
            event.preventDefault();
            const feature = event.selected[0];
            if (!feature) {
                return;
            }
            // Сбросить выбор, чтобы при следующем клике точка была доступна
            selectInteraction.getFeatures().clear();
            const object_id = feature.getId();
            const typeObject = feature.getProperties().typeObject;
            const coordinate = toLonLat(feature.getGeometry().getCoordinates());

            switch (typeObject) {
                case 'player':
                    // Отображаем информацию во всплывающем окне
                    Modal.showModal('Информация об игроке', await PlayerWindow.drawPlayerWindow(object_id));
                    break;
                case 'resources':
                    // Получаем информацию о точке с бэкенда
                    await websocketRequest(`/resource`, {
                        'action': 'get_resource',
                        'resource_id': object_id
                    }).then(resourceInfo => {
                        if (resourceInfo) {
                            // Отображаем информацию во всплывающем окне
                            Modal.showModal(resourceInfo?.name, `
                            <p>${resourceInfo?.description}</p>
                            <button class="resource-mine">Начать добычу</button>
                        `);
                            if (document.querySelector('.resource-mine')) {
                                document.querySelector('.resource-mine').onclick = (async (event) => {
                                    event.preventDefault();
                                    event.target.disabled = true;
                                    const responseMine = await websocketRequest(`/resource`, {
                                        'action': 'start_mine',
                                        'resource_id': object_id
                                    });
                                    // если майнинг начался без ошибок, то запускаем анимацию
                                    if (responseMine?.mine) {
                                        await animatedMine(object_id, resourceInfo.harvest_time_seconds, event);
                                    } else {
                                        Utils.createToast('Не удалось добыть. Попробуйте снова.');
                                        event.target.disabled = false;
                                    }
                                });
                            }
                        }
                    });
                    break;
                case 'monsters':
                    await getMonsterInfo(object_id);
                    break;
                case 'portals':
                    await getPortalInfo(object_id);
                    break;
                case 'npc':
                    const quest = await websocketRequest('/npc', {'action': 'get_npc', 'npc_id': object_id});
                    if (quest) {
                        const quest_id = quest.id;
                        // Отображаем информацию во всплывающем окне
                        Modal.showModal('Список квестов', Quest.generateQuestWindow([quest], 'accept'));
                        if (document.querySelector('.button-access')) {
                            document.querySelector('.button-access').onclick = async (e) => {
                                await websocketRequest('/quest', {'action': 'accept_quest', quest_id, object_id});
                                // сделаем заброс на проверку списка принятых квестов
                                Variable.setUserQuests(await websocketRequest('/quest', {'action': 'get_user_quest'}));
                                //localStorage.setItem('user_quests', JSON.stringify(Variable.getUserQuests()));
                                Quest.updateCountQuest(Variable.getUserQuests());
                                Modal.closeModalHandler(e);
                            };
                        }
                        if (document.querySelectorAll('.collapsible-header')) {
                            document.querySelectorAll('.collapsible-header').forEach(header => {
                                header.addEventListener('click', () => {
                                    const parent = header.parentElement;
                                    parent.classList.toggle('open');
                                });
                            });
                        }
                    }
                    break;
            }
        });


        // Добавление игрока на карту
        function addPlayerMarker(id, lon, lat, image) {
            const mpos = fromLonLat([lon, lat]);
            const feature = new Feature({
                geometry: new Point(mpos)
            });
            feature.setId(id);
            feature.setStyle(
                new Style({
                    image: new Icon({
                        src: '/img/' + image,
                        scale: 1,
                    }),
                })
            );
            feature.setProperties({
                typeObject: 'player'
            });
            playersSource.addFeature(feature);
        }

        // Добавление точек на карту
        async function drawPoints() {
            let boundBox = getBoundingBox(map);
            const nw = Utils.transformCoordinates(boundBox.nw);
            const se = Utils.transformCoordinates(boundBox.se);
            const z = parseInt(boundBox.zoom);
            //points = await apiRequest('/points/view', 'GET', {nw, se, z});
            points = await websocketRequest('/points', {'action': 'view', 'nw': nw, 'se': se, 'z': z});
            pointsSource.clear();
            if (!points) {
                pointsSource.clear();
            } else {
                points.forEach(function (item) {
                    const mpos = fromLonLat([item.coordinates.lat, item.coordinates.lon]);
                    const feature = new Feature({
                        geometry: new Point(mpos),
                    });
                    feature.setId('p' + item.id);
                    feature.setProperties({typeObject: item.type});

                    let style;
                    if (item.type === 'other') {
                        style = new Style({
                            image: Utils.createCircleStyle('rgba(64,64,64,0.62)', 10),
                            text: Utils.createTextStyle(item),
                        });
                    } else {
                        const iconPath =
                            item.type === 'monsters'
                                ? `/img/icons/points/monsters/${item.object_id}.png?${new Date().getDate()}`
                                : item.type === 'resources'
                                    ? `/img/icons/points/resources/${item.object_id}.png?${new Date().getDate()}`
                                    : item.type === 'portals'
                                        ? `/img/icons/points/portals/${item.object_id}.png?${new Date().getDate()}`
                                        : `/img/icons/points/${item.type}.png?${new Date().getDate()}`;

                        style = new Style({
                            image: Utils.createIconStyle(iconPath),
                            text: Utils.createTextStyle(item),
                        });
                    }

                    feature.setStyle(style);
                    pointsSource.addFeature(feature);
                });
            }
        }

        let timer;

        async function debounceDrawPoints() {
            clearTimeout(timer);
            timer = setTimeout(drawPoints, 200);
        }

        // Функция для получения координат текущего видимого квадрата
        function getBoundingBox(map) {
            const extent = view.calculateExtent(map.getSize());
            const nw = toLonLat(extent.slice(0, 2)).join(',');
            const se = toLonLat(extent.slice(2, 4)).join(',');
            const zoom = view.getZoom();
            return {nw, se, zoom};
        }

        document.querySelector('#toggle-follow').addEventListener("click", (e) => {
            e.preventDefault();
            if (e.currentTarget.getAttribute('data-active') === 'true') {
                e.currentTarget.setAttribute('data-active', false);
            } else {
                e.currentTarget.setAttribute('data-active', true);
            }
            localStorage.setItem('follow', e.currentTarget.getAttribute('data-active'));
        });

        document.querySelector('#button-inventory').addEventListener("click", (e) => {
            e.preventDefault();
            Modal.showModal(Variable.getSelfInfo().name, Utils.drawCharacterWindows(Variable.getSelfInfo()));
        });

        document.querySelector('#button-crafting').addEventListener("click", async (e) => {
            e.preventDefault();
            Variable.setUserRecipe(await websocketRequest('/recipe', {'action': 'get_recipes'}));
            Modal.showModal('Мастерская', DrawCrafting.drawCraftingWindow(Variable.getUserRecipe()));
            document.querySelectorAll('[data-craft-run]').forEach(btnCraft => {
                btnCraft.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.target.disabled = true;
                    const recipe_id = e.target.getAttribute('data-craft-run');
                    await websocketRequest('/recipe', {
                        'action': 'make_recipe',
                        'recipe_id': recipe_id
                    }).then(async response => {
                        if (response && response.crafting_time && response.crafting_time > 0) {
                            await DrawCrafting.animatedCraft(recipe_id, response.crafting_time, e);
                        } else {
                            e.target.disabled = false;
                        }
                    });
                });
            });
            const buttons = document.querySelectorAll('.craft-button');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    buttons.forEach(btn => btn.classList.remove('active'));
                    button.classList.add('active');
                    let itemType = button.getAttribute('data-item-type');
                    document.querySelectorAll('.recipe-item').forEach(recipeItem => {
                        if (recipeItem.getAttribute('data-item-type') === itemType) {
                            recipeItem.style.display = 'flex';
                        } else {
                            recipeItem.style.display = 'none';
                        }
                    });
                });
            });
        });

        document.querySelector('#button-settings').addEventListener("click", (e) => {
            e.preventDefault();
            Modal.showModal('Меню', `
                    <button id="button-profile">Профиль</button>
                    <button id="button-settings">Настройки игры</button>
                    <button id="button-feedback">Обратная связь</button>
                    <button id="button-logout">Выйти</button>
                `);
            document.querySelector('#button-logout').addEventListener("click", (e) => {
                e.preventDefault();
                Utils.logout();
            });
            document.querySelector('#button-profile').addEventListener("click", (e) => {
                e.preventDefault();
                Modal.showModal('Профиль', Profile.drawProfileWindow(), () => Profile.events());
            });
            document.querySelector('#button-settings').addEventListener("click", (e) => {
                e.preventDefault();
                Modal.showModal('Настройки', Settings.drawSettingsWindow(Variable.getSelfInfo().settings), () => Settings.events());
            });
            document.querySelector('#button-feedback').addEventListener("click", (e) => {
                e.preventDefault();
                Modal.showModal('Обратная связь', Feedback.drawFeedbackWindow(), () => Feedback.events());
            });
        });

        document.querySelector('#button-quest').addEventListener("click", (e) => {
            e.preventDefault();
            Modal.showModal('Список квестов', Quest.generateQuestWindow(Variable.getUserQuests(), 'view'));
            if (document.querySelectorAll('.collapsible-header')) {
                document.querySelectorAll('.collapsible-header').forEach(header => {
                    header.addEventListener('click', () => {
                        const parent = header.parentElement;
                        parent.classList.toggle('open');
                    });
                });
            }
            if (document.querySelector('.cancel-quest-button')) {
                document.querySelector('.cancel-quest-button').onclick = async (e) => {
                    e.preventDefault();
                    let quest_id = e.target.getAttribute('data-quest-id');
                    Modal.openConfirmModal(async () => {
                        await websocketRequest('/quest', {'action': 'delete_user_quest', quest_id});
                        //сделаем запрос на проверку списка принятых квестов
                        Variable.setUserQuests(await websocketRequest('/quest', {'action': 'get_user_quest'}));
                        //localStorage.setItem('user_quests', JSON.stringify(Variable.getUserQuests()));
                        Quest.updateCountQuest(Variable.getUserQuests());
                        Modal.closeModalHandler(e);
                    });
                };
            }
            if (document.querySelector('.complete-quest-button')) {
                document.querySelector('.complete-quest-button').onclick = async (e) => {
                    e.preventDefault();
                    let quest_id = e.target.getAttribute('data-quest-id');
                    await websocketRequest('/quest', {'action': 'complete_quest', quest_id});
                    //сделаем запрос на проверку списка принятых квестов
                    Variable.setUserQuests(await websocketRequest('/quest', {'action': 'get_user_quest'}));
                    //localStorage.setItem('user_quests', JSON.stringify(Variable.getUserQuests()));
                    Quest.updateCountQuest(Variable.getUserQuests());
                    //И обновим инфу об игроке. Инвентарь, серебро...
                    selfInfo = await websocketRequest('/player', {'action': 'get_self'});
                    Variable.setSelfInfo(selfInfo);
                    //localStorage.setItem('user_info', JSON.stringify(selfInfo));
                    Modal.closeModalHandler(e);
                };
            }
        });

        document.querySelector('#button-skill-progress').onclick = async (e) => {
            e.preventDefault();
            Modal.showModal('Прогресс', SkillProgress.drawProgressWindow(Variable.getSelfInfo()?.skill_progress));
        };

        document.querySelector('#button-stats-portal-close').onclick = async (e) => {
            e.preventDefault();
            Modal.showModal('Статистика', await Portal.getStats());
        };

        document.querySelector('#button-mail').onclick = async (e) => {
            e.preventDefault();
            await Mail.getMail();
        };

        document.querySelector('#button-market').onclick = async (e) => {
            e.preventDefault();
            await Market.draw();
        };

        // Событие движения карты
        map.on('moveend', debounceDrawPoints);

        // Событие изменения масштаба карты
        map.getView().on('change:resolution', debounceDrawPoints);

        await Chat.chat(true);
    });
});
