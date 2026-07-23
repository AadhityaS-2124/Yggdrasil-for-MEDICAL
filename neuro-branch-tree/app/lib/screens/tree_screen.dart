/// Screen 2: Tree display — results / loading / empty / error states.
///
/// Renders:
///   - Loading: skeleton cards + processing log
///   - Success: list of disease cards sorted by confidence_pct
///   - NoVerifiedData: honest empty-state with reason
///   - Error: clear, non-alarming error display

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../state/query_provider.dart';
import '../widgets/skeleton_card.dart';
import '../widgets/processing_log.dart';
import '../widgets/disease_card.dart';

class TreeScreen extends ConsumerWidget {
  const TreeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queryState = ref.watch(queryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Results'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            ref.read(queryProvider.notifier).reset();
            Navigator.of(context).pop();
          },
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: _buildBody(queryState, ref, context),
        ),
      ),
    );
  }

  Widget _buildBody(QueryState state, WidgetRef ref, BuildContext context) {
    switch (state.phase) {
      case QueryPhase.idle:
        return const Center(child: Text('Waiting for query...'));

      case QueryPhase.loadingStep1:
      case QueryPhase.loadingStep2:
      case QueryPhase.loadingStep3:
        return _buildLoadingState(state);

      case QueryPhase.success:
        return _buildSuccessState(state);

      case QueryPhase.noVerifiedData:
        return _buildNoDataState(state);

      case QueryPhase.error:
        return _buildErrorState(state, ref, context);
    }
  }

  Widget _buildLoadingState(QueryState state) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ProcessingLog(phase: state.phase),
        const SizedBox(height: 12),
        const Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: [
                SkeletonCard(),
                SkeletonCard(),
                SkeletonCard(),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessState(QueryState state) {
    final response = state.response!;
    final candidates = List.of(response.candidates)
      ..sort((a, b) => b.confidencePct.compareTo(a.confidencePct));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Extracted symptoms summary
        if (response.extractedSymptoms.isNotEmpty) ...[
          Text(
            'Recognized symptoms:',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: response.extractedSymptoms
                .map((s) => Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.indigo.shade50,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                            color: Colors.indigo.shade200, width: 0.5),
                      ),
                      child: Text(
                        s.replaceAll('_', ' '),
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.indigo.shade700,
                        ),
                      ),
                    ))
                .toList(),
          ),
          const SizedBox(height: 20),
        ],

        // Candidate count
        Text(
          '${candidates.length} candidate${candidates.length == 1 ? '' : 's'} found',
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),

        // Disease cards
        Expanded(
          child: ListView.builder(
            itemCount: candidates.length,
            itemBuilder: (context, index) => DiseaseCard(
              candidate: candidates[index],
              initiallyExpanded: index == 0,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildNoDataState(QueryState state) {
    final reason = state.noDataReason ?? 'unknown';
    final reasonText = reason == 'no_recognized_symptoms'
        ? 'No neurological symptoms were recognized in your description.'
        : reason == 'no_matching_disease_nodes'
            ? 'Symptoms were recognized, but no matching conditions were found in the verified dataset.'
            : 'Reason: $reason';

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded,
                size: 56, color: Colors.grey.shade400),
            const SizedBox(height: 20),
            const Text(
              'No verified clinical data available',
              key: Key('no_data_title'),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              reasonText,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'This is the system working as designed — it will not guess\nwhen there is insufficient evidence.',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade400,
                fontStyle: FontStyle.italic,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(
      QueryState state, WidgetRef ref, BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded,
                size: 56, color: Colors.grey.shade400),
            const SizedBox(height: 20),
            const Text(
              'Something went wrong',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              state.errorMessage ?? 'Unknown error',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey.shade600,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            OutlinedButton.icon(
              onPressed: () {
                ref.read(queryProvider.notifier).reset();
                Navigator.of(context).pop();
              },
              icon: const Icon(Icons.arrow_back),
              label: const Text('Go back'),
            ),
          ],
        ),
      ),
    );
  }
}
