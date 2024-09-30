//
//  SquareView.swift
//  ollama_test
//
//  Created by 지영C 이 on 9/30/24.
//

import SwiftUI

struct SquareView: View {
    @State var isVisible: Bool
    
    var body: some View {
        VStack {
            Button(action: {
                isVisible.toggle()
            }, label: {
                Text("show/hide")
            })
            
            Text("보인다")
                .opacity(isVisible ? 1 : 0)
        }
    }
}

#Preview {
    SquareView(isVisible: true)
}
