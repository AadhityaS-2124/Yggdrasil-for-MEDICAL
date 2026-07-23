/// Phase 6b widget tests.
///
/// Tests confirm:
///   1. Skeleton cards render during loading states
///   2. Processing log shows correct text for each loading step
///   3. Probability badge renders differently for 5% vs 88%
///   4. Disease card shows "unreviewed dataset" footer conditionally

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:neuro_branch_tree/models/disease_node.dart';
import 'package:neuro_branch_tree/state/query_provider.dart';
import 'package:neuro_branch_tree/widgets/skeleton_card.dart';
import 'package:neuro_branch_tree/widgets/processing_log.dart';
import 'package:neuro_branch_tree/widgets/probability_badge.dart';
import 'package:neuro_branch_tree/widgets/disease_card.dart';

void main() {
  // -----------------------------------------------------------------------
  // SkeletonCard tests
  // -----------------------------------------------------------------------
  group('SkeletonCard', () {
    testWidgets('renders during loading', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Column(
              children: [SkeletonCard(), SkeletonCard(), SkeletonCard()],
            ),
          ),
        ),
      );

      // Should find 3 skeleton cards (3 Card widgets from skeleton cards)
      final cards = find.byType(SkeletonCard);
      expect(cards, findsNWidgets(3));
    });

    testWidgets('has animated opacity', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: Scaffold(body: SkeletonCard())),
      );

      // Find the Opacity widget used for shimmer
      expect(find.byType(Opacity), findsOneWidget);

      // Pump a few frames to verify animation runs without error
      await tester.pump(const Duration(milliseconds: 600));
      await tester.pump(const Duration(milliseconds: 600));
    });
  });

  // -----------------------------------------------------------------------
  // ProcessingLog tests
  // -----------------------------------------------------------------------
  group('ProcessingLog', () {
    testWidgets('shows correct text for loadingStep1', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProcessingLog(phase: QueryPhase.loadingStep1),
          ),
        ),
      );

      expect(find.text('Step 1/3: Dissecting language...'), findsOneWidget);
    });

    testWidgets('shows correct text for loadingStep2', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProcessingLog(phase: QueryPhase.loadingStep2),
          ),
        ),
      );

      expect(
          find.text('Step 2/3: Searching Neurology Index...'), findsOneWidget);
    });

    testWidgets('shows correct text for loadingStep3', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProcessingLog(phase: QueryPhase.loadingStep3),
          ),
        ),
      );

      expect(
          find.text('Step 3/3: Calculating probability...'), findsOneWidget);
    });

    testWidgets('renders nothing for non-loading phases', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ProcessingLog(phase: QueryPhase.idle),
          ),
        ),
      );

      expect(find.byType(SizedBox), findsOneWidget);
      expect(find.text('Step 1/3: Dissecting language...'), findsNothing);
    });
  });

  // -----------------------------------------------------------------------
  // ProbabilityBadge tests
  // -----------------------------------------------------------------------
  group('ProbabilityBadge', () {
    testWidgets('renders 5% with muted gray style', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ProbabilityBadge(confidencePct: 5)),
        ),
      );

      expect(find.text('5%'), findsOneWidget);

      // Get the Container decoration
      final container = tester.widget<Container>(find.byKey(const Key('probability_badge')));
      final decoration = container.decoration as BoxDecoration;

      // Low confidence: gray background
      expect(decoration.color, Colors.grey.shade200);
    });

    testWidgets('renders 88% with prominent teal style', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ProbabilityBadge(confidencePct: 88)),
        ),
      );

      expect(find.text('88%'), findsOneWidget);

      final container = tester.widget<Container>(find.byKey(const Key('probability_badge')));
      final decoration = container.decoration as BoxDecoration;

      // High confidence: teal background
      expect(decoration.color, const Color(0xFF0D9488));
    });

    testWidgets('5% and 88% have different font sizes', (tester) async {
      // Render 5%
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ProbabilityBadge(confidencePct: 5)),
        ),
      );
      final text5 = tester.widget<Text>(find.text('5%'));
      final fontSize5 = text5.style!.fontSize;

      // Render 88%
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ProbabilityBadge(confidencePct: 88)),
        ),
      );
      final text88 = tester.widget<Text>(find.text('88%'));
      final fontSize88 = text88.style!.fontSize;

      // 88% should have a larger font than 5%
      expect(fontSize88! > fontSize5!, true,
          reason: '88% ($fontSize88) should be larger than 5% ($fontSize5)');
    });

    testWidgets('30% renders with amber mid-tier style', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: ProbabilityBadge(confidencePct: 30)),
        ),
      );

      expect(find.text('30%'), findsOneWidget);

      final container = tester.widget<Container>(find.byKey(const Key('probability_badge')));
      final decoration = container.decoration as BoxDecoration;

      // Mid confidence: amber background
      expect(decoration.color, Colors.amber.shade100);
    });
  });

  // -----------------------------------------------------------------------
  // DiseaseCard tests
  // -----------------------------------------------------------------------
  group('DiseaseCard', () {
    final unreviewedCandidate = CandidateNode(
      diseaseId: 'parkinsons_disease',
      namePlain: "Parkinson's Disease",
      confidencePct: 88,
      pathognomonicMatches: const ['resting_tremor', 'bradykinesia'],
      supportingMatches: const [],
      variants: const [Variant(name: 'Tremor-dominant', notes: 'Resting tremor is prominent.')],
      treatments: const ['Levodopa/carbidopa'],
      source: 'Adams and Victor\'s Principles of Neurology',
      clinicalReviewStatus: 'unreviewed',
    );

    final reviewedCandidate = CandidateNode(
      diseaseId: 'migraine',
      namePlain: 'Migraine',
      confidencePct: 5,
      pathognomonicMatches: const [],
      supportingMatches: const ['headache'],
      clinicalReviewStatus: 'reviewed',  // hypothetical future value
    );

    testWidgets('shows name and probability badge when collapsed',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: DiseaseCard(candidate: unreviewedCandidate),
            ),
          ),
        ),
      );

      expect(find.text("Parkinson's Disease"), findsOneWidget);
      expect(find.text('88%'), findsOneWidget);
    });

    testWidgets('shows unreviewed footer when expanded and status is unreviewed',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: DiseaseCard(
                candidate: unreviewedCandidate,
                initiallyExpanded: true,
              ),
            ),
          ),
        ),
      );

      expect(
        find.text('Unreviewed dataset — for architecture demonstration only'),
        findsOneWidget,
      );
    });

    testWidgets('does NOT show unreviewed footer when status is reviewed',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: DiseaseCard(
                candidate: reviewedCandidate,
                initiallyExpanded: true,
              ),
            ),
          ),
        ),
      );

      expect(
        find.text('Unreviewed dataset — for architecture demonstration only'),
        findsNothing,
      );
    });

    testWidgets('expands on tap to show details', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: DiseaseCard(candidate: unreviewedCandidate),
            ),
          ),
        ),
      );

      // Before tap: footer should not be visible (collapsed)
      expect(
        find.text('Unreviewed dataset — for architecture demonstration only'),
        findsNothing,
      );

      // Tap to expand
      await tester.tap(find.byType(InkWell));
      await tester.pumpAndSettle();

      // After tap: footer should be visible
      expect(
        find.text('Unreviewed dataset — for architecture demonstration only'),
        findsOneWidget,
      );
    });

    testWidgets('shows variant details when expanded', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: DiseaseCard(
                candidate: unreviewedCandidate,
                initiallyExpanded: true,
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // The "Variants" section header is a plain Text widget
      expect(find.text('Variants'), findsOneWidget);

      // The variant name is inside a RichText → TextSpan
      final richTextFinder = find.byWidgetPredicate((widget) {
        if (widget is RichText) {
          final text = widget.text.toPlainText();
          return text.contains('Tremor-dominant');
        }
        return false;
      });
      expect(richTextFinder, findsOneWidget);
    });
  });
}
