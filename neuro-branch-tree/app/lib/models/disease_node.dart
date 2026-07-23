/// Data models mirroring the backend's Pydantic response models exactly.
/// Field names match main.py's QueryResponse / CandidateResponse 1:1
/// so there's no silent mismatch between backend and frontend contracts.

class Variant {
  final String name;
  final String notes;

  const Variant({required this.name, this.notes = ''});

  factory Variant.fromJson(Map<String, dynamic> json) {
    return Variant(
      name: json['name'] as String,
      notes: (json['notes'] as String?) ?? '',
    );
  }
}

class CandidateNode {
  final String diseaseId;
  final String namePlain;
  final int confidencePct;
  final List<String> pathognomonicMatches;
  final List<String> supportingMatches;
  final List<Variant> variants;
  final List<String> treatments;
  final String source;
  final String clinicalReviewStatus;

  const CandidateNode({
    required this.diseaseId,
    required this.namePlain,
    required this.confidencePct,
    this.pathognomonicMatches = const [],
    this.supportingMatches = const [],
    this.variants = const [],
    this.treatments = const [],
    this.source = '',
    this.clinicalReviewStatus = 'unreviewed',
  });

  factory CandidateNode.fromJson(Map<String, dynamic> json) {
    return CandidateNode(
      diseaseId: json['disease_id'] as String,
      namePlain: json['name_plain'] as String,
      confidencePct: json['confidence_pct'] as int,
      pathognomonicMatches:
          (json['pathognomonic_matches'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      supportingMatches:
          (json['supporting_matches'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      variants:
          (json['variants'] as List<dynamic>?)
              ?.map((e) => Variant.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      treatments:
          (json['treatments'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      source: (json['source'] as String?) ?? '',
      clinicalReviewStatus:
          (json['clinical_review_status'] as String?) ?? 'unreviewed',
    );
  }
}

class AnalyzeResponse {
  final String status;
  final String reason;
  final List<String> extractedSymptoms;
  final List<CandidateNode> candidates;

  const AnalyzeResponse({
    required this.status,
    this.reason = '',
    this.extractedSymptoms = const [],
    this.candidates = const [],
  });

  factory AnalyzeResponse.fromJson(Map<String, dynamic> json) {
    return AnalyzeResponse(
      status: json['status'] as String,
      reason: (json['reason'] as String?) ?? '',
      extractedSymptoms:
          (json['extracted_symptoms'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      candidates:
          (json['candidates'] as List<dynamic>?)
              ?.map((e) => CandidateNode.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  bool get isOk => status == 'OK';
  bool get isNoVerifiedData => status == 'NO_VERIFIED_DATA';
}
