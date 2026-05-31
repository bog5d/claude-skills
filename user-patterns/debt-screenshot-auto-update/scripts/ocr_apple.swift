#!/usr/bin/env swift
import Vision
import CoreImage
import Foundation

guard CommandLine.arguments.count > 1 else {
    print("Usage: ocr_apple.swift <image_path>")
    exit(1)
}

let imagePath = CommandLine.arguments[1]
let url = URL(fileURLWithPath: imagePath)

guard let ciImage = CIImage(contentsOf: url) else {
    print("ERROR: Cannot load image at \(imagePath)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(ciImage: ciImage, options: [:])
try handler.perform([request])

guard let results = request.results else {
    print("")
    exit(0)
}

for observation in results {
    if let candidate = observation.topCandidates(1).first {
        print(candidate.string)
    }
}
