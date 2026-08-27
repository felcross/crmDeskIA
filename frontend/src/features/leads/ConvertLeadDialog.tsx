import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { convertLead } from "@/api/leads";
import type { LeadResponse } from "@/types/api";

const schema = z.object({
  valor: z.coerce.number().positive("Valor deve ser maior que zero"),
  pipeline: z.string().optional(),
  estagio: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface ConvertLeadDialogProps {
  lead: LeadResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ConvertLeadDialog({
  lead,
  open,
  onOpenChange,
}: ConvertLeadDialogProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      valor: undefined,
      pipeline: "default",
      estagio: "Prospecção",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: FormValues) => convertLead(Number(lead.id), data),
    onSuccess: () => {
      toast.success(`Lead "${lead.nome}" convertido em negócio!`);
      queryClient.invalidateQueries({ queryKey: ["dashboard", "deals"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "leads"] });
      reset();
      onOpenChange(false);
    },
    onError: (err: Error) => {
      toast.error(err.message || "Erro ao converter lead");
    },
  });

  function onSubmit(data: FormValues) {
    mutation.mutate(data);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent aria-describedby="convert-lead-desc">
        <DialogHeader>
          <DialogTitle>Converter em negócio</DialogTitle>
          <DialogDescription id="convert-lead-desc">
            Criar um novo negócio a partir do lead <strong>{lead.nome}</strong>.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="valor">Valor (R$) *</Label>
            <Input
              id="valor"
              type="number"
              step="0.01"
              placeholder="5000.00"
              {...register("valor")}
            />
            {errors.valor && (
              <p className="text-sm text-destructive">{errors.valor.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="pipeline">Pipeline</Label>
            <Input
              id="pipeline"
              placeholder="default"
              {...register("pipeline")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="estagio">Estágio inicial</Label>
            <Input
              id="estagio"
              placeholder="Prospecção"
              {...register("estagio")}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={mutation.isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Converter
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
