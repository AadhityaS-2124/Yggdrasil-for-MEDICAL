/// Inline processing step indicator tied to query_provider phases.
///
/// Reads directly from the existing QueryPhase enum — no new timing logic.
/// Shows a subtle animated dot + step text during loading states.

import 'package:flutter/material.dart';
import '../state/query_provider.dart';

class ProcessingLog extends StatelessWidget {
  final QueryPhase phase;

  const ProcessingLog({super.key, required this.phase});

  String get _text {
    switch (phase) {
      case QueryPhase.loadingStep1:
        return 'Dissecting language...';
      case QueryPhase.loadingStep2:
        return 'Searching Neurology Index...';
      case QueryPhase.loadingStep3:
        return 'Calculating probability...';
      default:
        return '';
    }
  }

  int get _stepNumber {
    switch (phase) {
      case QueryPhase.loadingStep1:
        return 1;
      case QueryPhase.loadingStep2:
        return 2;
      case QueryPhase.loadingStep3:
        return 3;
      default:
        return 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_text.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              value: null,
              color: Colors.indigo.shade300,
            ),
          ),
          const SizedBox(width: 10),
          Text(
            'Step $_stepNumber/3: $_text',
            key: const Key('processing_log_text'),
            style: TextStyle(
              fontSize: 13,
              fontStyle: FontStyle.italic,
              color: Colors.grey.shade600,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }
}
