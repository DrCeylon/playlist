// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Resonance",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        .library(name: "ResonanceCore", targets: ["ResonanceCore"]),
        .library(name: "ResonanceDesign", targets: ["ResonanceDesign"]),
        .executable(name: "ResonanceMac", targets: ["ResonanceMac"]),
    ],
    targets: [
        .target(
            name: "ResonanceCore",
            path: "ResonanceCore/Sources/ResonanceCore"
        ),
        .target(
            name: "ResonanceDesign",
            dependencies: ["ResonanceCore"],
            path: "ResonanceDesign/Sources/ResonanceDesign",
            resources: [
            .copy("Resources/themes"),
        ],
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
            sources: ["Sources/ResonanceMac"],
            resources: [
                .copy("Resources/Assets"),
            ]
        ),
        .testTarget(
            name: "ResonanceCoreTests",
            dependencies: ["ResonanceCore"],
            path: "ResonanceCore/Tests/ResonanceCoreTests"
        ),
        .testTarget(
            name: "ResonanceMacTests",
            dependencies: ["ResonanceMac", "ResonanceCore", "ResonanceDesign"],
            path: "ResonanceMac/Tests/ResonanceMacTests"
        ),
    ]
)
