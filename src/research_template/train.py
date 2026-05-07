"""Entry point for model training."""

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
        # TODO: Build dataset and dataloader
        # TODO: Build model
        # TODO: Build optimizer and scheduler
        # TODO: Run training loop, logging with: wandb.log({"loss": loss, "acc": acc})
        # TODO: Save checkpoints to output_dir/checkpoints/
        raise NotImplementedError("Training loop is not yet implemented.")
    finally:
        wandb.finish()


if __name__ == "__main__":
    main()
