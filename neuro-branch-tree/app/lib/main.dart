import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'screens/input_screen.dart';

void main() {
  runApp(const ProviderScope(child: NeuroBranchTreeApp()));
}

class NeuroBranchTreeApp extends StatelessWidget {
  const NeuroBranchTreeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Neurology Branching Tree',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const InputScreen(),
    );
  }
}
