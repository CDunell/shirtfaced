// The scene pipeline is now direct vertical coverage: a scene owns a small set
// of native 9:16 first frames, up to five of which can be approved and animated.
// The legacy single-master -> 3x3 contact-sheet -> panel-extraction backend stays
// available for old records, but it is no longer the production UI.
export { SceneShotsBench as ScenesBench } from "./SceneShotsBench";
