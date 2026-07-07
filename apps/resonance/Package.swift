// swift-tools-version: 5.9
import PackageDescription

var products: [Product] = [
    .library(name: "ResonanceCore", targets: ["ResonanceCore"]),
]

var targets: [Target] = [
    .target(
        name: "ResonanceCore",
        path: "ResonanceCore/Sources/ResonanceCore"
    ),
    .testTarget(
        name: "ResonanceCoreTests",
        dependencies: ["ResonanceCore"],
        path: "ResonanceCore/Tests/ResonanceCoreTests"
    ),
]

#if !os(Linux)
products.append(contentsOf: [
    .library(name: "ResonanceDesign", targets: ["ResonanceDesign"]),
    .executable(name: "ResonanceMac", targets: ["ResonanceMac"]),
])

targets.append(contentsOf: [
    .target(
        name: "ResonanceDesign",
        dependencies: ["ResonanceCore"],
        path: "ResonanceDesign/Sources/ResonanceDesign",
        resources: [
            .copy("Resources/themes"),
        ]
    ),
    .testTarget(
        name: "ResonanceDesignTests",
        dependencies: ["ResonanceDesign"],
        path: "ResonanceDesign/Tests/ResonanceDesignTests"
    ),
    .executableTarget(
        name: "ResonanceMac",
        dependencies: ["ResonanceCore", "ResonanceDesign"],
        path: "ResonanceMac",
        exclude: [
            "Tests",
            "Resources/Info.plist",
            "Resources/AppIcon.iconset",
        ],
        sources: ["Sources/ResonanceMac"],
        resources: [
            .copy("Resources/Assets"),
        ]
    ),
    .testTarget(
        name: "ResonanceMacTests",
        dependencies: ["ResonanceMac", "ResonanceCore", "ResonanceDesign"],
        path: "ResonanceMac/Tests/ResonanceMacTests"
    ),
])
#endif

let package = Package(
    name: "Resonance",
    platforms: [
        .macOS(.v14),
    ],
    products: products,
    targets: targets
)
