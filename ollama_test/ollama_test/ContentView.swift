//
//  ContentView.swift
//  ollama_test
//
//  Created by 지영C 이 on 9/30/24.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, world!")
            SquareView(isVisible: true)
        }
        .padding()
    }
}

#Preview {
    ContentView()
}
