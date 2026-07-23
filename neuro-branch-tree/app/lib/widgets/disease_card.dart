/// Expandable disease candidate card.
///
/// Collapsed: name_plain + probability_badge
/// Expanded: name_clinical, matched vs unmatched symptoms (visually distinct),
///           variants, treatments, source, and conditional unreviewed footer.
///
/// The "unreviewed dataset" footer is wired to the ACTUAL clinical_review_status
/// field — not hardcoded unconditionally — so it auto-corrects once real data
/// is reviewed.

import 'package:flutter/material.dart';
import '../models/disease_node.dart';
import 'probability_badge.dart';

class DiseaseCard extends StatefulWidget {
  final CandidateNode candidate;
  final bool initiallyExpanded;

  const DiseaseCard({
    super.key,
    required this.candidate,
    this.initiallyExpanded = false,
  });

  @override
  State<DiseaseCard> createState() => _DiseaseCardState();
}

class _DiseaseCardState extends State<DiseaseCard> {
  late bool _expanded;

  @override
  void initState() {
    super.initState();
    _expanded = widget.initiallyExpanded;
  }

  CandidateNode get c => widget.candidate;

  @override
  Widget build(BuildContext context) {
    return Card(
      key: Key('disease_card_${c.diseaseId}'),
      elevation: _expanded ? 3 : 1,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => setState(() => _expanded = !_expanded),
        child: AnimatedSize(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeInOut,
          alignment: Alignment.topCenter,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // --- Collapsed header (always visible) ---
              _buildHeader(),
              // --- Expanded content ---
              if (_expanded) _buildExpandedContent(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: Text(
              c.namePlain,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(width: 12),
          ProbabilityBadge(confidencePct: c.confidencePct),
          const SizedBox(width: 8),
          AnimatedRotation(
            turns: _expanded ? 0.5 : 0.0,
            duration: const Duration(milliseconds: 200),
            child: Icon(
              Icons.expand_more,
              color: Colors.grey.shade500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExpandedContent() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Divider
          Divider(color: Colors.grey.shade200, height: 1),
          const SizedBox(height: 12),

          // Clinical name
          Text(
            c.diseaseId.replaceAll('_', ' ').toUpperCase(),
            style: TextStyle(
              fontSize: 11,
              color: Colors.grey.shade500,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),

          // --- Symptom matches ---
          if (c.pathognomonicMatches.isNotEmpty) ...[
            _sectionTitle('Pathognomonic matches', Icons.check_circle,
                const Color(0xFF0D9488)),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: c.pathognomonicMatches
                  .map((s) => _symptomChip(s, matched: true, pathognomonic: true))
                  .toList(),
            ),
            const SizedBox(height: 12),
          ],

          if (c.supportingMatches.isNotEmpty) ...[
            _sectionTitle('Supporting matches', Icons.check_circle_outline,
                Colors.amber.shade700),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: c.supportingMatches
                  .map((s) => _symptomChip(s, matched: true, pathognomonic: false))
                  .toList(),
            ),
            const SizedBox(height: 12),
          ],

          // --- Variants ---
          if (c.variants.isNotEmpty) ...[
            _sectionTitle('Variants', Icons.account_tree, Colors.indigo.shade400),
            const SizedBox(height: 6),
            ...c.variants.map((v) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('•  ', style: TextStyle(color: Colors.grey.shade500)),
                      Expanded(
                        child: RichText(
                          text: TextSpan(
                            style: DefaultTextStyle.of(context).style,
                            children: [
                              TextSpan(
                                text: v.name,
                                style: const TextStyle(fontWeight: FontWeight.w500),
                              ),
                              if (v.notes.isNotEmpty)
                                TextSpan(
                                  text: ' — ${v.notes}',
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 13,
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
            const SizedBox(height: 12),
          ],

          // --- Treatments ---
          if (c.treatments.isNotEmpty) ...[
            _sectionTitle('Treatments', Icons.medication, Colors.blue.shade400),
            const SizedBox(height: 6),
            ...c.treatments.map((t) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      Text('•  ', style: TextStyle(color: Colors.grey.shade500)),
                      Expanded(
                        child: Text(t, style: const TextStyle(fontSize: 14)),
                      ),
                    ],
                  ),
                )),
            const SizedBox(height: 12),
          ],

          // --- Source ---
          if (c.source.isNotEmpty) ...[
            Text(
              'Source: ${c.source}',
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey.shade500,
                fontStyle: FontStyle.italic,
              ),
            ),
            const SizedBox(height: 12),
          ],

          // --- Clinical review status footer ---
          if (c.clinicalReviewStatus == 'unreviewed')
            Container(
              key: const Key('unreviewed_footer'),
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.orange.shade200, width: 0.5),
              ),
              child: Text(
                'Unreviewed dataset — for architecture demonstration only',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.orange.shade700,
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),
            ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String title, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Text(
          title,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: color,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }

  Widget _symptomChip(String tag, {required bool matched, required bool pathognomonic}) {
    final label = tag.replaceAll('_', ' ');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: pathognomonic
            ? const Color(0xFF0D9488).withValues(alpha: 0.1)
            : Colors.amber.shade50,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: pathognomonic
              ? const Color(0xFF0D9488).withValues(alpha: 0.3)
              : Colors.amber.shade200,
          width: 0.5,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: pathognomonic ? const Color(0xFF0D9488) : Colors.amber.shade800,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
