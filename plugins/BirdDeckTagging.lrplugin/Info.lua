return {
    LrSdkVersion = 13.0,
    LrSdkMinimumVersion = 13.0,
    LrToolkitIdentifier = 'de.birdtagging.lightroom',
    LrPluginName = 'BirdDeck Tagging',
    LrInitPlugin = 'Init.lua',
    LrForceInitPlugin = true,
    LrEnablePlugin = 'Init.lua',
    LrDisablePlugin = 'Shutdown.lua',
    LrLibraryMenuItems = {
        { title = 'Start / Restart BirdDeck Tagging', file = 'Init.lua' },
    },
    LrShutdownPlugin = 'Shutdown.lua',
    VERSION = { major = 0, minor = 2, revision = 0, build = 1 },
}
