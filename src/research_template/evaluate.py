"""Entry point for model evaluation."""

import wandb
import hydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf

from research_template.utils.logging import get_logger
from research_template.utils.seed import set_seed


@hydra.main(version_base=None, config_path="../../configs", config_name="config")
def main(cfg: DictConfig) -> None:
    logger = get_logger(__name__)
    set_seed(cfg.seed)

    output_dir = HydraConfig.get().runtime.output_dir
    logger.info(f"Output dir: {output_dir}")
    logger.info(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    run = wandb.init(
        project=cfg.wandb.project,
        entity=cfg.wandb.get("entity") or None,
        mode=cfg.wandb.get("mode", "online"),
        config=OmegaConf.to_container(cfg, resolve=True),
        dir=output_dir,
    )

    try:
        # TODO: Load model from checkpoint (e.g., output_dir/checkpoints/best.pth)
        # TODO: Build eval dataloader
        # TODO: Run evaluation loop
        # TODO: Compute metrics and log with: wandb.log({"val/acc": acc, "val/loss": loss})
        # TODO: Save metrics to output_dir/metrics.json
        raise NotImplementedError("Evaluation loop is not yet implemented.")
    finally:
        wandb.finish()


if __name__ == "__main__":
    main()
