import { useEffect, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material';

import { BusinessWorkflowApiError, useDecisionFeedback, type DecisionFeedbackRequest } from '../../api';

const maximumCommentLength = 1000;

function feedbackErrorMessage(error: unknown) {
  if (!(error instanceof BusinessWorkflowApiError)) return 'Geribildirim kaydedilemedi. Bağlantınızı kontrol edip tekrar deneyin.';
  if (error.kind === 'feedback-invalid') return 'Geribildirim bilgisi doğrulanamadı. Lütfen seçiminizi ve yorumunuzu kontrol edin.';
  if (error.kind === 'execution-unavailable') return 'Bu karar artık erişilebilir değil.';
  if (error.kind === 'unauthorized') return 'Oturumunuz sona ermiş olabilir. Lütfen tekrar giriş yapın.';
  return 'Geribildirim kaydedilemedi. Lütfen tekrar deneyin.';
}

export function DecisionFeedback({ executionId, snapshotId }: { executionId: string; snapshotId: string }) {
  const feedback = useDecisionFeedback();
  const [feedbackType, setFeedbackType] = useState<DecisionFeedbackRequest['feedback_type']>();
  const [comment, setComment] = useState('');

  useEffect(() => {
    setFeedbackType(undefined);
    setComment('');
    feedback.reset();
  }, [snapshotId]);

  const submit = () => {
    if (!feedbackType) return;
    const payload: DecisionFeedbackRequest = {
      feedback_type: feedbackType,
      ...(comment.trim() ? { comment: comment.trim() } : {}),
    };
    feedback.mutate({ executionId, snapshotId, payload });
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={1.5}>
          <Box>
            <Typography component="h3" variant="h6">Bu öneri yararlı mıydı?</Typography>
            <Typography variant="body2" color="text.secondary">Geribildiriminiz bu karar kaydına eklenir.</Typography>
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant={feedbackType === 'HELPFUL' ? 'contained' : 'outlined'} disabled={feedback.isPending} aria-pressed={feedbackType === 'HELPFUL'} onClick={() => { setFeedbackType('HELPFUL'); feedback.reset(); }}>
              Yararlı
            </Button>
            <Button variant={feedbackType === 'NOT_HELPFUL' ? 'contained' : 'outlined'} color={feedbackType === 'NOT_HELPFUL' ? 'secondary' : 'primary'} disabled={feedback.isPending} aria-pressed={feedbackType === 'NOT_HELPFUL'} onClick={() => { setFeedbackType('NOT_HELPFUL'); feedback.reset(); }}>
              Yararlı değil
            </Button>
          </Stack>
          {feedbackType && <>
            <TextField
              label="İsteğe bağlı yorum"
              multiline
              minRows={3}
              value={comment}
              onChange={(event) => setComment(event.target.value.slice(0, maximumCommentLength))}
              helperText={`${comment.length}/${maximumCommentLength}`}
              slotProps={{ htmlInput: { maxLength: maximumCommentLength } }}
              disabled={feedback.isPending}
            />
            <Button variant="contained" onClick={submit} disabled={feedback.isPending} aria-label="Geribildirimi kaydet">
              {feedback.isPending ? 'Geribildirim kaydediliyor…' : 'Geribildirimi kaydet'}
            </Button>
          </>}
          {feedback.isSuccess && <Alert severity="success" role="status">{feedback.data.status === 'ALREADY_EXISTS' ? 'Bu geribildiriminiz zaten kaydedilmiş.' : 'Geribildiriminiz kaydedildi.'}</Alert>}
          {feedback.isError && <Alert severity="warning" action={<Button color="inherit" size="small" onClick={submit} disabled={!feedbackType || feedback.isPending}>Tekrar dene</Button>}>{feedbackErrorMessage(feedback.error)}</Alert>}
        </Stack>
      </CardContent>
    </Card>
  );
}
