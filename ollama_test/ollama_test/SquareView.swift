//
//  SquareView.swift
//  ollama_test
//
//  Created by 지영C 이 on 9/30/24.
//

import SwiftUI

struct SquareView: View {
    @State var isVisible: Bool
    @State var textColor: Color
    
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
        
        VStack {
            Text("Hi")
        }
    }
}

#Preview {
    SquareView(isVisible: true, textColor: .green, backgroundColor: .red)
}
